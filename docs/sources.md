# Sources and provenance

## Verification ledger

| Claim | Label | Evidence |
| --- | --- | --- |
| XTS 2500 enumerates as USB CDC-ACM `0cad:1001` | [V] | measured `lsusb`/`lsusb -v` in the independent open-astro-cps hardware ground-truth notes |
| AT identity/mode sequence | [V] | live radio transcripts and captured serial dump |
| PPP/IPCP + RCMP transport | [V] | live capture and pcap decoding |
| Codeplug `.cpg` is OLE2/CFB with `AdkFileHeader`/`Strm_N` | [C] | parsed real codeplugs and byte-for-byte round trip |
| RCMP write record + CRC-16/CCITT | [C] | 147 captured writes reproduced byte-exact |
| Auth LFSR challenge/response | [C] | 3 captured pairs + live radio |
| Partition map `0x80`/`0x81`/`0x82`/`0x85` | [C] | PatPort.exe schema and live reads/writes |
| 137-record complete read for `H46UCF9PW6BN` | [C] | hardware read, CRC-ok |
| XTS 2500 is an ASTRO 25 "Patriot" dual-core MCU+DSP | [V] | XTS 2500 Detailed Service Manual 6816985H01-F, section 4.1.6.1.1 |
| Host MCU is "MCORE-based" | [V] | XTL 5000 manual + M\*CORE RAM downloader; XTS 2500 manual calls it a 32-bit MCU |
| Patriot FlashZap RAM downloader is M\*CORE big-endian | [V] | `mcore-elf` binutils reads `elf32-mcore-big`, "Motorola RCE" |
| U800 Patriot, U803 flash, U804 SRAM, U701 MAKO pinouts | [V] | XTS 2500 Detailed Service Manual chapters 4/8/9 |
| SRAM 1 MB, 19 addr/16 data, CS2; flash 8 MB early / 64 MB later, CS0 | [V] | XTS 2500 Detailed Service Manual 4.1.6.1.2–3 and parts lists |
| 96×64 LCD, EIM D0–D7, 7×3 keypad | [V] | XTS 2500 Detailed Service Manual 4.1.6.3.4 |
| Encryption "Armour" module, 40-pin, SSI, keyfill pin 34 | [V] | XTS 2500 Detailed Service Manual 4.1.6.3.5 |
| Firmware split host S-record + DSP `.ish` | [V] | FlashZap preferences and strings |
| FlashZap targets Intel W18-B 4/8/16 MB | [V] | strings in Patriot RAM downloader |
| `.cvn` has plaintext header then high-entropy payload | [V] | direct inspection |
| `.cvn` is consumed by CPS/Depot FLASHport rather than FlashZap client | [U] | no `.cvn` strings in FlashZap; needs confirmation |
| DSP is DSP56300 | [U] | community claim, no primary evidence; do not rely |
| Physical partition addresses (`0x10020000`, etc.) | [U] | secondary docs; schema is item/partition based |

## Vendor files archived locally (not redistributed)

All of these are in `firmware/` or `docs/vendor/` and are git-ignored. Hashes
are in `firmware/SHA256SUMS.txt` and `firmware/MANIFEST.md`.

| File | Source path |
| --- | --- |
| XTS2500 `DVN4136M`, `R09.00.05`, `DVN4228S/W/Y`, `DVN4301B`, `DVN4301J R20.50.09` | Windows `the local firmware archive` and Desktop |
| XTS5000 `DVN4225Y`, `DVN4274G`, `DVN4274P R20.50.09`, `R09.00.05`, `R15.00.00` | same |
| `astro25_flashzap_for_astro25_radios_admin_admin.rar` | same |
| XTS 2500/1500/MT1500/PR1500 Detailed Service Manual 6816985H01-F | supplied by the project owner; now `docs/vendor/` |
| XTS 5000 Detailed Service Manual 6881094C31-E | supplied by the project owner; now `docs/vendor/` |
| XTL 5000 Basic Service Manual 6881096C73-O | the local service-manual archive; now `docs/vendor/` |

Do not commit these files. They are vendor material kept for interoperability
research only.

## FCC filings

Public exhibits (internal photos, operational descriptions, some schematics):

- https://fccid.io/AZ489FT5816 — 806–870 MHz, original XTS2500 filing
- https://fccid.io/AZ489FT5804 — 764–870 MHz, multiple Class II changes
- https://fccid.io/AZ489FT3807 — 136–174 MHz VHF
- https://fccid.io/AZ489FT4865 — 380–470 MHz UHF
- https://fccid.io/AZ489FT5849 — 896–901 / 935–940 MHz

Internal photos are low resolution; they cannot resolve chip markings.

## External research repositories

- `RivasMario/open-astro-cps` — independent ASTRO 25 RCMP/AT/tuning research,
  virtual radio server, codeplug parser. **Caution:** its own `docs/README.md`
  marks several docs as fabricated; use only the verified/capture-backed files.
- `nyaaaaaaatalie/OpenAutoBench` — Astro 25 tuning tests and commands.
  Deprecated; successor is `jelimoore/OpenAutoBench-ng`.
- `W9CR/Astro-CP-Decoder` — Astro Spectra/Astro Saber/XTS3000 binary codeplug
  decoder (not XTS2500, but useful historical context).
- `KFDtool/KFDtool` — open P25 key fill device; relevant to UCM/keyfill.
- `dvmproject` / `DSD` / `OP25` — P25 infrastructure and receive-side research,
  not radio firmware.

## Toolchain references

- Binutils M\*CORE opcode table and disassembler:
  `opcodes/mcore-opc.h`, `opcodes/mcore-dis.c` in binutils-gdb.
- GCC M\*CORE backend: `gcc/config/mcore/`.
- GDB M\*CORE simulator: `sim/mcore/interp.c`.
- Sourceware gitweb example:
  https://sourceware.org/git/?p=binutils-gdb.git;a=blob_plain;f=opcodes/mcore-opc.h;hb=HEAD
- GNU binutils release used for local analysis: 2.45.

## Software sources used to derive the codeplug/protocol facts

- `PatPort.exe` / `PatPortDepot.exe` (CPS/Depot) for schema, partitions, and
  FLASHcode.
- `NextGen10.dll` for RCMP bundler/COM surface and unlock.
- `cgIsh10c.dll` / `fhAdk10c.dll` / `udcIsh10c.dll` for ISH layout, `.cpg`
  crypto, and record checksums.
- `ByteData10.dll` / `RadioCustStack10.dll` for PPP/TCP transport constants.
- Real XTS 2500 codeplugs and USB captures.

No vendor source is included here. The clean-room rule applies: observations,
specifications, and independent implementations only.

## Service manual search status

See [service-manual-search.md](service-manual-search.md). Both detailed service
manuals are now present:

| File | SHA-256 (prefix) | Bytes |
| --- | --- | ---: |
| `XTS2500_XTS1500_MT1500_PR1500_Detailed_Service_Manual_6816985H01-F.pdf` | `b460d936…` | 76,696,093 |
| `XTS5000_Detailed_Service_Manual_6881094C31-E.pdf` | `0b0081ee…` | 21,311,656 |

The Basic Service Manual `6816984H01` is still not present, but the detailed
manual contains the schematics, board overlays, pinouts, and parts lists needed
for emulation and reverse engineering.
