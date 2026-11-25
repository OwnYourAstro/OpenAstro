# Research log

## 2026-11-24 — initial research and archive

### Sources reviewed

- Prior clean-room codeplug/protocol work (`.cpg`, RCMP, auth, partitions).
- `RivasMario/open-astro-cps` verified docs (hardware ground truth, RCMP wire,
  AT discovery, `.cpg` format, tuning, virtual radio).
- `OpenAutoBench` Astro 25 tuning interface and soft-pot commands.
- XTL 5000 Basic Service Manual 6881096C73-O (ASTRO 25 family).
- FCC filings for the XTS2500 family (internal photos, operational
  descriptions).
- Windows drive firmware archive.

### Actions

1. Mounted the Windows NTFS partition read-only at
   `/run/media/rose/C464FAA464FA987E`.
2. Located firmware under `Users/Rose/Documents/Motorola Firmware` and Desktop.
3. Copied XTS2500/XTS5000 `.cvn` files, R09 zip packages, FlashZap tool, and
   the XTL 5000 service manual into `OpenAstro/firmware` and
   `OpenAstro/docs/vendor`.
4. Generated `firmware/SHA256SUMS.txt`, then unmounted the partition.
5. Extracted the FlashZap RAR and the R09 zip packages.
6. Found FlashZap RAM downloaders for `patriot` and `omap16xx`.
7. Converted the Patriot RAM downloader S-record to ELF; confirmed
   `elf32-mcore-big` / "Motorola RCE".
8. Built `mcore-elf` binutils 2.45 to disassemble it.
9. Inspected FlashZap preferences, PSDT/tuner XML, ishbrowser schema, and
   strings for boot/flash behaviour.
10. Inspected `.cvn` headers and entropy; payload is encrypted/compressed.
11. Read the XTL 5000 manual's controller theory and glossary: Patriot IC is a
    dual-core MCU+DSP; host is MCORE-based; MDI is the internal MCU/DSP bus.

### Key results

- Host CPU family is M\*CORE, not ColdFire/ARM.
- Firmware is split host S-record + DSP `.ish`.
- FlashZap is the factory RAM/flash path; Intel W18-B flash.
- `.cvn` extraction is the main blocker for code analysis.
- The XTS 2500 service manual was initially missing; it was supplied later the
  same day (see below).

### Service manual acquisition and review (same day)

The project owner supplied two detailed service manuals at the repository root.
They were renamed and moved to `docs/vendor/`:

- `XTS2500_XTS1500_MT1500_PR1500_Detailed_Service_Manual_6816985H01-F.pdf`
  (914 pages, 76.7 MB, SHA-256 `b460d936…`)
- `XTS5000_Detailed_Service_Manual_6881094C31-E.pdf`
  (374 pages, 21.3 MB, SHA-256 `0b0081ee…`)

Review results:

- The XTS 2500 manual explicitly documents **Patriot U800**: 256-pin BGA,
  32-bit MCU + 16-bit DSP, 1.875 V core/EIM and 2.9 V I/O, 16.8 MHz + 32.768 kHz
  clocks.
- MCU: 22.5K×32 internal RAM, 1K×32 boot ROM, EIM 24 addr/16 data/6 CS, two SPI
  buses/10 CS, two UARTs, one-wire, MDI.
- DSP: 84K×24 program RAM, 62K×16 data RAM, BBP, DSP timer, SAP.
- SRAM U804: 1 MB, 19 addr/16 data, EIM CS2.
- Flash U803: EIM CS0, 8 MB in early theory text, 64 MB in later parts lists;
  contains host firmware, DSP firmware, codeplug, tuning values.
- MAKO U701: 176-pin BGA, regulators, 16-bit CODEC, audio PA, 10-bit ADC, USB
  transceiver, watchdog, one-wire, side connector.
- Display: 96×64 LCD, EIM D0–D7, CS, write, address 0; keypad 7×3 (18 keys).
- Encryption module: Armour IC, 40-pin connector, SSI, keyfill pin 34, 16 keys.
- The XTS 5000 manual confirms the same Patriot concept (U401/U402/U403/U500/
  U501) and supplies a second EIM/memory block diagram.

A FlashZap capability review found **Read Memory** (`FZAPworker::readMemory`,
`readmem.srec`) with S-record output. This is now the preferred way to obtain
the deployed host/DSP images without decrypting `.cvn`.

The absolute EIM base addresses, boot-ROM behaviour, and DSP ISA remain
unknown.

### Next

- Save and review all notes (this document set).
- Try `.cvn` extraction/decryption via CPS/Depot captures or static analysis.
- Build a RAM-downloader conformance test using GDB `sim/mcore` / a standalone
  M\*CORE interpreter.
- Recover the absolute memory map and boot vectors from a firmware/boot dump.
- Map MAKO/RF/DSP register behaviour as evidence arrives.

## 2026-11-24 — `.cvn` decrypted

Instrumented installed ASTRO 25 Portable Depot R20.01.00 with Frida while it
selected `XTS2500_DVN4301J_R20.50.09.cvn`.

Key results:

- `EncatenComponent.dll` (SysWOW64) is the file-package component; decryption
  uses Windows CryptoAPI. `authAES.dll` is not used for this file.
- `CryptDecrypt` outputs a 34,602,556-byte plain XML `filePackage`.
- The package contains host `RAPP R20.50.09` (load `0x10210000`, 2,791,612
  bytes after flattening), DSP2/DSPB `R19.50.01` (load `0x10080000`),
  CFWI `R07.11.12` (load `0x01600000`), PSDT, and per-band tuning records.
- Host vector table starts at `0x10210000`; first entry is `0x10210210`.
- `.cvn` requires no iButton/FLASHkey for this software path. The later
  FLASHkey dialog was a radio timeout caused by debugger pauses.

Added `tools/extract_file_package.py` and extracted all unique package items
under the git-ignored `firmware/extracted/` tree.

## 2026-11-24 — Host R20.50.09 static analysis

Built `mcore-elf` binutils 2.45 and converted the extracted RAPP S-record to
`elf32-mcore-big`.

Confirmed:

- Host load `0x10210000`, end `0x104B98BC`, reset vector `0x10210210`.
- Vector table at `0x10210000`; exception trampoline at `0x10210276`.
- Boot chain `0x10218470 → 0x10224718 → 0x102111C8 → 0x102102F0`.
- The application callback `0x102183BC` is installed at `0x1200BFE8` and is
  invoked from the kernel bootstrap after timer setup `0x102181E8`.
- `0x10436084` is `memcpy`; `0x10436128` `memset`; `0x10436188` `strcpy`;
  `0x104361C8` `strcmp`.
- AT dispatcher at `0x10222140`, including `AT#FZAP=0..3`.
- Service report at `0x1021EF36` prints `R20.50.09`; serial/Flashcode report
  starts near `0x1021F1F4`.
- Plaintext strings confirm the normal CPS/radio application is present.

Details are in `docs/host-r20.50.09.md`. The local `host.dis` and `.elf` remain
in the git-ignored extracted tree.

- Kernel bootstrap `0x102102F0` constructs 32-byte task control blocks and
  68-byte initial stack frames from an 8-byte task table (priority, stack size,
  entry point) referenced through `0x12000018`; `0x12000028` is the initial
  stack pointer and `0x12000014` the TCB base.

- Traced `AT#FZAP=0..3` from the AT dispatcher (`0x102221CC`) to handler
  `0x10219834`. It writes a `"Boot"` marker, selects 57.6/115.2/230.4/460.8
  kbaud, sets `0x1200086A = 1`, and enters the reset path at `0x10231DC4`.

- The PSDT parser at `0x102260D8` gets its base from `0x12000770`, checks
  `PHDR` at `+0xE000`, and walks `CPLG`/`SECP`/`TUNE` records at `PSDT+0x60`.
  It calls ROM entry `0x1004F4`; early setup calls ROM `0x100104`. Those ROM
  entries and the boot-filled `0x12000000` block are the missing runtime state.