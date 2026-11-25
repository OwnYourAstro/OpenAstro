# XTS 2500 firmware notes

## 1. Firmware is split in two

ASTRO 25 is a two-processor design: a host application on the Patriot MCU and a
DSP image on the Patriot DSP. FlashZap's preferences name the split directly:

```
HOST (Portable)   Z:\sub_oa_releases\patriarch\portable\astro_portable.srec
HOST (Mobile)     Z:\sub_oa_releases\patriarch\mobile\astro_mobile.srec
DSP (CodeRed)     Z:\digital_core_release\dsp\codered.ish
DSP (Bravo)       Z:\digital_core_release\dsp\bravo.ish
RAM downloader    Z:\sub_oa_releases\component\flashzap\fzap_flash_ram_dloader.srec
```

The host image is an **S-record**; the DSP image is an **`.ish`** file. The
host image is the part that runs the UI, AT interface, codeplug, and control
logic. The DSP image runs the modem/vocoder/audio work.

The XTS 2500 service manual identifies the external flash as **U803**, connected
to EIM `CS0_N`, and states that it contains host firmware, DSP firmware,
codeplug data, and tuning values. Early board descriptions say **8 MB**; later
parts lists show **64 MB** devices. Verify the exact size per kit before
building a flash model. See [hardware.md](hardware.md) §4.

`FlashZap` also names two Patriot variants:

- `Patriot HIP7 (Bravo)`
- `Patriot CDR3 (RAM22)`

and has a separate `omap16xx` RAM downloader for other (non-Patriot) products.

## 2. Host CPU: Motorola M\*CORE

The FlashZap RAM downloader for Patriot is M\*CORE. Reproduce:

```sh
# Extract the S-record from the FlashZap RAR, then convert:
objcopy -I srec -O elf32-mcore-big \
  'Flashzap/ramdl/patriot/fzap_flash_ram_dloader.srec' patriot.elf
file patriot.elf
# ELF 32-bit MSB relocatable, Motorola RCE, version 1 (SYSV), stripped
objdump -D patriot.elf | less
```

Measured properties of the RAM downloader:

| Property | Value |
| --- | --- |
| S-record header | `SWINFOFFRD01.04.20` (the `.1x` variant is `R04.00.00`) |
| Load range | `0x00100400`–`0x001057bb` |
| Entry | `0x00100500` |
| Endianness | Big-endian (`elf32-mcore-big`) |
| Architecture | Motorola M\*CORE / "Motorola RCE" |
| Embedded strings | `FlashZap Downloader`, `Intel W18-B 4MB`, `8MB`, `16MB`, `RS-232 115.2 kbps`, `USB Operation`, `Ready to Program` |

M\*CORE tooling status:

- Binutils still has `mcore-elf` BFD targets and a disassembler
  (`opcodes/mcore-dis.c`, `opcodes/mcore-opc.h`).
- GCC still has `gcc/config/mcore/` (M\*CORE machine description, M210/M340,
  big/little endian).
- GDB still has `sim/mcore/interp.c`, a functional instruction interpreter.

This is the single most useful result for the emulator: a working reference
CPU model already exists in GDB's simulator, and a compiler exists in GCC.

## 3. `.cvn` firmware containers

The archived XTS 2500 update packages are `.cvn` files:

| File | Approx. size |
| --- | --- |
| `XTS2500_R09.00.03_DVN4136M.zip` (contains `.cvn`) | 7.1 MB |
| `XTS2500_R09.00.05.zip` (contains `.cvn`) | 7.1 MB |
| `XTS2500_DVN4228S.cvn` | 15 MB |
| `XTS2500_DVN4228W.cvn` | 17 MB |
| `XTS2500_DVN4228Y.cvn` | 17 MB |
| `XTS2500_DVN4301B.cvn` | 17 MB |
| `XTS2500_DVN4301J_R20.50.09.cvn` | 17 MB |

Observations:

- The first bytes are plaintext ASCII:
  `Copyright (c) 2011 Motorola, Inc. All rights reserved.` (year varies).
- Around offset `0x43` there is a short ASCII code such as `0-LM-6`.
- After roughly `0x4c` the payload reaches **~8.0 bits/byte entropy in every
  sampled block**, which indicates encryption rather than plain compression.
  `tools/cvn_probe.py` can reproduce this.
- Comparing versions with `cmp`/`xxd` shows no usable plaintext deltas.
- No S-record text (`S0`/`S3`) survives in the container.
- The FlashZap client does not advertise `.cvn` in its UI strings; `.cvn` is
  more likely consumed by CPS/Depot's FLASHport path or by the radio boot
  application. This is **[U]** and needs confirmation.

### Decryption result (2026-11-24)

`.cvn` decryption is done **on the PC** by Depot, not by the radio and not by
FlashZap. The relevant component is the installed
`C:\Windows\SysWOW64\EncatenComponent.dll` (Motorola file-package component),
which uses Windows CryptoAPI. `authAES.dll` is not on this path.

A live Depot R20.01.00 FLASHport attempt was instrumented with Frida. The
`CryptDecrypt` output was captured before the radio port failed. It unwraps to a
plain XML `filePackage` containing S-record `fileData` items:

- RAPP host: `R20.50.09`, load `0x10210000`, end `0x104B98BC`
- DSP2 CodeRed: `R19.50.01`, load `0x10080000`, 327,680 bytes
- DSPB Bravo: `R19.50.01`, load `0x10080000`, 327,680 bytes
- CFWI MACE boot app: `R07.11.12`, load `0x01600000`
- PSDT: `R04.00.00`, load `0x1000E000`
- per-band TUNE records

The host image begins with a 32-bit vector table at `0x10210000`; the first
entry is `0x10210210`, followed by exception vectors. This is the first
verified host image available for emulator work.

See [host-r20.50.09.md](host-r20.50.09.md) for the static analysis, boot chain,
RTOS bootstrap addresses, library routines, and host strings.

Reproduce locally:

```sh
python3 tools/extract_file_package.py \
  firmware/extracted/XTS2500_R20.50.09.decrypted.xml \
  firmware/extracted/package
python3 tools/srec2bin.py \
  'firmware/extracted/package/RAPP-R20.50.09-H46.......BN.srec' \
  firmware/extracted/XTS2500_R20.50.09_RAPP.bin
```

Extracted vendor images stay in the git-ignored `firmware/extracted/` tree.
Do **not** distribute them.

The FLASHkey error seen later was a port/radio timeout response after the
instrumented process was paused; this `.cvn` had already been unwrapped by the
software and did not require an iButton or FLASHkey dongle.

## 4. FlashZap: the factory flash path

`astro25_flashzap_for_astro25_radios_admin_admin.rar` contains the FLASHZap
client `R01.28.00` (April 2008). Important capabilities visible in its strings
and ReadMe:

- SBEP/RCMP transport over serial or USB, including boot mode.
- RAM downloader (`fzap_flash_ram_dloader.srec`) loaded into target RAM.
- Erase/program/verify flash, flash markers, boot application.
- **Read Memory** (`FZAPworker::readMemory`), `readmem.srec`, and S-record
  output. This is the least invasive way to obtain the deployed host/DSP images
  without decrypting `.cvn`.
- `Boot Load and Unlock`, `Unlock the FlashZap security features`.
- PSDT (platform-specific data table) read and checksum.
- S-record parsing, combined CRC verification, S7 entry handling.
- Remote/gang flashing, auto RAM downloader, FlashZap autotuner.
- `Read PSDT`, `Extract codeplug`, `Read reset capture`, `ISH browser`.

This is the path to run code on real hardware without writing the main
firmware first: boot the RAM downloader, then load a test S-record into RAM.
That is the ideal first open-firmware milestone.

## 5. Boot and update flow (working model)

```
power-on
  └─ boot ROM / boot application
       ├─ normal: load and start host application from flash
       └─ programming/boot mode:
            ├─ SBEP/RCMP session, unlock
            ├─ load RAM downloader into RAM
            ├─ erase/program flash (S-records)
            ├─ write flash markers / PSDT
            └─ reset to new application
```

The Patriot MCU has a small internal **1K × 32 boot ROM**; the external flash is
the application store. The boot ROM's entry point and verification behaviour
are still unknown.

Details still unknown:

- Whether the boot ROM enforces a signature/MAC on host or DSP images.
- Where the flash markers live and what they validate.
- The exact handoff between host and DSP at boot.
- Whether the RAM downloader is accepted only in a special boot mode or via an
  unlock challenge.

## 6. Firmware version evidence

The XTS 5000 serial dump in the archive (`Read XTS5000-serial-dump.spm`) shows
the AT identity reply with:

```
RADIO:XTS 5000
MODEL:H18QDH9PW7AN
SERIAL:320CEN7470
R19.50.C
R01.0C
```

The first line is the host/radio software version; the second is likely the
DSP or boot version. Exact field mapping needs confirmation from the XTS 2500.

## 7. DSP image

The service manual describes the DSP side of the Patriot as a **16-bit DSP**
with **84K × 24 bits program RAM** and **62K × 16 bits data RAM**, a Baseband
Interface Port (BBP), a DSP timer, and a Serial Audio Codec Port (SAP). It does
not name the DSP core or ISA.

The `.ish` extension appears for `codered.ish` and `bravo.ish`. Possibilities:

- a Motorola ISH (image/loader) container with its own CRC/header;
- a raw DSP image wrapped in the same ISH item format used by the codeplug;
- a compressed/encrypted DSP payload.

This is **[U]**. We need either a DSP `.ish` sample, the service manual's DSP
part number, or a flash dump. Do not assume DSP56300.

## 8. Firmware-related safety

- Never write partition `0x82` (calibration).
- A failed host flash can leave the radio in boot mode or unbootable; FlashZap
  and a known-good `.cvn` are the recovery path.
- A failed DSP flash produces DSP-related FAIL codes (e.g. `FAIL 02/81 DSP ROM
  checksum` in the XTL 5000 manual).
- Keep a full codeplug and tuning backup before any experiment.
