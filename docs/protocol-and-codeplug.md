# Host protocol, codeplug, and tuning

This document is about talking to a **running** radio. Replacing the firmware
is covered in [open-firmware-plan.md](open-firmware-plan.md).

## 1. Transport stack

The common ASTRO 25 programming stack is:

```
USB CDC-ACM (or USB-UART on XTS 5000/mobiles)
  └─ AT command mode
       └─ PPP (LCP/IPCP)
            └─ RCMP
                 └─ ISH object/item reads and writes
```

### 1.1 AT identity and mode switch

A known-good XTS 2500 sequence is:

1. Open the port at 9600 8N1, RTS/CTS.
2. `AT&V` returns:

```
CARRIER:9600
PROTOCOL:ALT
COMPRESSION:NONE
FLOW:K3
WV304:192.168.128.1
RADIO:XTS 2500
MODEL:H46UCF9PW6BN
SERIAL:[serial redacted]
PORT:SIDE CONNECTOR AS RS232
SECURE:R000000
CPS:HARDWARE FLOW CONTROL
OK
```

3. Close/reopen; `AT#DATLCL=1` → `OK`.
4. Close/reopen; `AT+IPR=115200` → `OK`; port changes to 115200.
5. Close/reopen; send `CLIENT`; radio replies `CLIENTSERVER`.
6. Start PPP. The host becomes `192.168.128.2`; the radio is
   `192.168.128.1`.

Some tools instead dial with `ATD` and use a RAS/pppd link. Both behaviours are
seen; the `CLIENT` path is the one used by the codeplug writer.

### 1.2 RCMP framing

RCMP has appeared in more than one framing depending on the transport and CPS
generation. Do not hard-code one without checking the session.

Observed forms:

```
A. PPP/TCP session (one verified XTS 2500 capture):
   request : 0c seq(2) cmd flags(2) len(1) data[len]
   response: 1c seq(2) cmd flags(2) len(1) data[len]

B. Length-prefixed record:
   [u16_be length][opcode(2)][payload...]

C. Older TCP/tuner style:
   [u16_be length][payload...]
```

The stable part is: a big-endian length, a 16-bit opcode, and a response that
echoes the opcode with bit 15 set (`0x0100` → `0x8100`).

### 1.3 Opcodes (verified subset)

| Opcode | Direction | Meaning |
| --- | --- | --- |
| `0x0100` | host → radio | Read ISH object/block |
| `0x0101` | host → radio | Write ISH object/block |
| `0x0102` | host → radio | Prepare/write pre-step |
| `0x0103` | host → radio | Erase/prepare `DelIshTypes` |
| `0x0106` | host → radio | Session open (`...00`) / commit+end (`...01`) |
| `0x0107` | host → radio | Security unlock / challenge-response |
| `0x0001` / `0x0002` | host → radio | Older read/write object form |
| `0x0010` / `0x0011` / `0x0012` | host → radio | Model / serial / UUID query |
| `0x81xx` | radio → host | ACK/response to `0x01xx` |

There are also 2-byte command forms seen in older tuner tools:

```
00 01 02 01 <softpot>   set/write a soft-pot
00 01 03 11             read power soft-pot tables
00 02 10                analog mode
00 02 11 / 00 02 12     low/high tone
```

Treat these as tuner-session commands, not ordinary codeplug RCMP.

### 1.4 Read/write records

A verified write record shape is:

```
01 01 <part:1> <tag:2> <inst:2> <len:2> 00 00 <len:2> <payload> <crc:2>
```

- `len` counts payload + 2-byte CRC.
- CRC is CRC-16/CCITT, polynomial `0x1021`, init `0x0000`, non-reflected,
  big-endian, over the payload.
- Observed partitions written: `0x80` and `0x81`. Never `0x82`.
- A read reply contains a 12-byte echoed header + payload + 2-byte CRC.

### 1.5 Session and commit

The codeplug writer sequence, verified on an XTS 2500:

1. `AT&V`, `AT#DATLCL=1`, `AT+IPR=115200`, `CLIENT`, PPP.
2. RCMP `01 06 00` begin; config/program-mode records.
3. Auth `03 00` → 32-byte challenge; `03 01 <response>`.
4. Program mode `01 08 81`; write config records.
5. Write the **entire** record set: identity records first, `0x0047` last.
6. Reorg/commit `01 07 80 00`.
7. End `01 06 01`; the radio returns to normal mode.

Writing a subset leaves the ISH directory inconsistent (`FAIL 01/02`).
Writing a wrong layout can drop identity (`FAIL 01/92`).

### 1.6 Security challenge

The 32-byte auth response is an LFSR transform, verified against captured
challenge/response pairs and live hardware:

```
state = 0x51E88D21
for k in 0..31:
    b = challenge[k]
    rev = challenge[31-k]
    for bit in 7..1:
        fb = ((rev >> bit) & 1) ^ ((state >> 9) & 1)
        state = (state * 2 + fb) & 0xFFFFFFFF
        b ^= (fb << bit)
    response[k] = b
```

`state` is seeded once per auth. The radio replies `83 00 00 <32>` to the
challenge request and `83 01 00` to the response.

This is the **partition unlock** challenge. It is not the same thing as a
firmware signature check.

## 2. Codeplug file format (`.cpg`)

### 2.1 Container

`.cpg` is a Microsoft OLE2 Compound File (CFB), the same container as legacy
`.doc`/`.xls`.

```
/AdkFileHeader       800-byte CFhAdkFileHeader (plaintext)
/DataStg/Strm_0      stream directory / map
/DataStg/Strm_1..N   one stream per ISH record
```

The header contains the model string, serial string, UUID, encryption type,
header version, and a header checksum. Real codeplugs carry e.g.
`H46UCF9PW6BN` / `[serial redacted]`.

### 2.2 Stream directory

`Strm_0` (after decryption) is `N` 10-byte big-endian entries plus a 2-byte
trailer:

```
u32 id          virtual address / record id
u16 type        (v1) 0x0080 normally, 0x0081 for identity records
u16 checksum    (v2) equals the record stream's trailing u16
u16 stream      (v3) the Strm_<n> ordinal
```

The directory checksum is `(sum(entries) + 0xAAAB) & 0xFFFF`, big-endian.

### 2.3 Data record

```
u32 id
u16 len            == payload_len + 2
u8  payload[len-2]
u16 checksum       CRC-16/CCITT poly 0x1021, init 0x0000, big-endian
```

The record id is also the directory key and the first map field.

### 2.4 Encryption

Two encryption types are seen:

- **Legacy custom cipher** (`encType 0`) — a PRNG/escaping cipher used for an
  18-byte key blob and older whole files. The 9-byte seed is sometimes ASCII
  (`A8Z6J9QP5` in public samples). The algorithm is documented in the earlier
  clean-room notes.
- **Windows CryptoAPI RC4** (`encType 1`) — real R20 codeplugs. Seed is hashed
  with MD5, a 40-bit RC4 key is derived via `CryptDeriveKey(CALG_RC4)`, and each
  `Strm_N` is independently encrypted. The Microsoft provider's RC4 output does
  not match textbook RC4 for the same key bytes, so the clean-room implementation
  uses the same Windows CSP or reproduces its exact behaviour.

Do not assume a `.cpg` stream is textbook RC4 without checking the encryption
type and provider.

### 2.5 Tags and records

The model is item/partition based. For a hardware-tested 700/800 XTS 2500
(`H46UCF9PW6BN`) the complete read was **137 records / 96 distinct tags**.
A corpus of 33 codeplugs covered **149 tags with no unmapped records**.

Representative tags:

| Tag | Content |
| --- | --- |
| `0x000A` | Radio Wide |
| `0x0020` | Controls / buttons |
| `0x0047` | ISH directory/reorg record (must be written last) |
| `0x0FA1` | Scan-list membership |
| `0x0FFB` | Conventional personality |
| `0x0FFD` | Zone channel assignment / channel records |
| `0x0FFF` | Channel names |
| `0x1004` | Identity (serial/model) in partition `0x81` |
| `0x1005` | 43-byte feature bitmask |
| `0x1006` | ASCII FLASHcode |

Frequencies in channel records are 32-bit big-endian words in 5 Hz units
(`Hz = word * 5`).

### 2.6 FLASHcode

- ASCII string at `0x81:1006:0`; binary bitmask at `0x81:1005:0`.
- Format `AAAAAA-BBBBBB-C`; 12 hex nibbles = 48 feature bits.
- Check digit is Luhn mod-10 over the 12 nibble values, even positions doubled.
- Q667 (ADP software encryption) is nibble 8, bit 4.
- The 43-byte `0x1005` bitmask layout is still opaque; the ASCII FLASHcode is
  the authoritative feature list.

Writing `0x81` requires the unlock path; an ordinary codeplug write is ACKed
but the bootloader may drop it.

## 3. Tuning (`.tun`) and soft-pots

`.tun` files are **not** OLE2; they are raw MFC `CArchive` serialization.

- Serial and model strings are length-prefixed.
- Around `0x50` is an MFC class tag `CSaveValues` and the band edge.
- Calibration blocks start at `0x010A`: 26 fixed-size 170-byte tables, each
  with a marker, a 32-bit parameter type, a sub-index, and up to 16
  `(frequency word, DAC value)` pairs. Frequencies are again 5 Hz units.

Tuning pot numbers from FlashZap's `tunerinfo.xml` (700/800 Millennium
transceiver):

| Pot | Function |
| --- | --- |
| 0 | Reference oscillator |
| 1 | Power detection calibration |
| 2 | TX deviation balance |
| 4 | TX current limit |
| 5 | TX deviation limit |
| 7 | TX power characterization |

`0x82` is per-radio calibration. It is not recoverable without a service
monitor and the factory alignment procedure. Every tool must refuse writes to
`0x82`.

## 4. Crypto and key fill

- **ADP**: software 40-bit RC4, key can live in the codeplug, algorithm ID
  `0xAA`. Weak by design; not real confidentiality.
- **DES-OFB / DES-XL / AES-256**: hardware UCM only, algorithm IDs `0x81`,
  `0x80`, `0x84`. The codeplug stores algorithm, key ID, and slot/SLN/CKR
  references; the key bytes are loaded separately over the 3-wire keyfill path
  using a KVL/KFD.
- The side connector's keyfill pin and the TIA-102.AACA protocol are the path
  for a software keyloader. KFDtool is an open implementation for the host side.

## 5. Failure modes worth knowing

| Display | Meaning |
| --- | --- |
| `FAIL 01/02` | Codeplug/ISH directory inconsistent (often an incomplete write) |
| `FAIL 01/92` | Codeplug identity block missing/invalid |
| `FAIL 01/82` | Calibration/checksum problem (danger zone) |
| `FAIL 02/81` | DSP ROM checksum (reflash DSP) |
| `FAIL 02/88` | DSP RAM fatal |
| `FAIL 02/90` | General DSP hardware |

Recovery from `01/02` or `01/92` needs a complete, verified codeplug for the
exact model/serial. It is not a firmware fault and a FLASHport update will not
fix it.

## 6. Protocol gaps

- Exact RCMP framing differs by session type and CPS generation; build a
  transport that can be selected per capture.
- The full directory read path is still needed to trust a radio-read codeplug
  as a write source.
- Network/OTAP programming uses a .NET Remoting variant with a DES-wrapped
  channel; same operations, different transport.
- The radio has both a UUID and a password in the network API; the password
  path is not mapped.
