# OpenAstro

Research and engineering notes for two related goals:

1. **An XTS 2500 emulator** — run/inspect the radio's firmware and reproduce its
   behaviour without a radio.
2. **Open-source firmware for an XTS 2500** — a replacement host application
   (and, later, DSP/RF work) that runs on real hardware.

This repository is currently a **research archive**, not a working emulator or
firmware. It records what is known, what was measured, where the evidence came
from, and what is still missing.

> **Safety and legal**
>
> Programming or flashing a radio can brick it. The tuning partition (`0x82`)
> holds per-radio RF calibration and must never be written by experiments.
> Vendor firmware and service documents are kept locally for interoperability
> research only and are not redistributed. `IMBE`/`AMBE` voice codecs are
> patented by DVSI; a clean-room P25 voice path needs a licensing decision.
> Nothing here is affiliated with or endorsed by Motorola Solutions.

## Status at a glance

| Area | State |
| --- | --- |
| Codeplug / CPS protocol | **Read and write verified** on one XTS 2500 by this project's prior clean-room work |
| AT / PPP / RCMP transport | **Verified** against real hardware and captures |
| Hardware architecture | **Confirmed from the XTS 2500 Detailed Service Manual**: Patriot U800 dual-core MCU+DSP |
| Host CPU ISA | **Verified for the FlashZap RAM downloader: Motorola M\*CORE** |
| DSP ISA / peripherals | DSP memory/interfaces documented; exact DSP core/ISA still unknown |
| Firmware images | **Extracted/decrypted:** host RAPP `R17.00.02` and `R20.50.09`, DSP2/DSPB `R17.00.02`/`R19.50.01`, CFWI, PSDT, tuning |
| Host firmware analysis | **Started:** reset/vector table, RTOS bootstrap, task builder, AT dispatcher, library routines |
| Emulator | **M\*CORE simulator built:** boots R17 host through RTOS init, application callback, and the 87-entry task table; stock UI is blocked on missing low-ROM/application-RAM state |
| Firmware decryption | **Reusable tool added:** `tools/decrypt_cvn.py` captures Depot `CryptDecrypt` output without a FLASHkey or radio write |
| Open firmware | Not built; toolchain and flash path partially identified |

## Key findings

- The XTS 2500 is a native **USB CDC-ACM** device (`0cad:1001`), not an FTDI
  cable. It speaks AT, then PPP, then RCMP on `192.168.128.1:8002`.
- The XTS 2500 uses a **"Patriot" IC (U800)**: a 256-pin BGA dual-core device
  containing a 32-bit MCU and a 16-bit DSP (XTS 2500 Detailed Service Manual
  6816985H01-F, section 4.1.6.1.1). The MCU is MCORE-based; the DSP has
  84K×24 program RAM and 62K×16 data RAM.
- The **FlashZap** RAM downloader for the Patriot platform is **M\*CORE**
  big-endian code. This was confirmed by converting its S-record to ELF and
  disassembling with `mcore-elf` binutils (`elf32-mcore-big`, "Motorola RCE").
- Firmware is split into a **host application S-record** and a **DSP image**
  (`codered.ish`, `bravo.ish` appear in FlashZap's preferences). The host image
  and DSP image are separate update artifacts.
- XTS 2500 firmware update packages are `.cvn` files. Depot on Windows unwraps
  them through `EncatenComponent.dll`/CryptoAPI into a plain XML file package.
  Host, DSP, CFWI, PSDT, and tuning images have been extracted; no iButton or
  FLASHkey is required for this software path.
- FlashZap exposes the factory flash path: SBEP/RCMP, RAM downloader, flash
  erase/program, flash markers, unlock, boot application, and a PSDT
  (platform-specific data table). It targets Intel W18-B 4/8/16 MB flash.
- The codeplug format, partitions, auth challenge, RCMP framing, CRC, and write
  session are already documented and implemented in this project's prior
  clean-room codeplug work.
- The **XTS 2500 Detailed Service Manual** (`6816985H01-F`, 914 pages) and the
  **XTS 5000 Detailed Service Manual** (`6881094C31-E`, 374 pages) are now
  archived locally. They provide the Patriot/SRAM/flash/MAKO pinouts, display
  and keypad wiring, encryption-module interface, test points, schematics,
  board overlays, and parts lists.

## What is in this repository

```
README.md                     This overview
docs/00-index.md              Document map and evidence labels
docs/service-manual-review.md What the XTS 2500/XTS 5000 manuals contain
docs/hardware.md              Radio, board, memory, USB, RF, crypto hardware
docs/firmware.md              Image formats, FlashZap, M*CORE, .cvn analysis
docs/protocol-and-codeplug.md AT/PPP/RCMP, .cpg, tuning, partitions
docs/emulator-plan.md         Emulator design, phased plan, risks
docs/EMULATOR_STATUS.md       Current emulator status, evidence, and blocker
docs/open-firmware-plan.md    Custom firmware design, toolchain, flash path
docs/gaps.md                  Prioritised missing knowledge
docs/sources.md               Provenance, URLs, hashes, verification ledger
docs/research-log.md          Chronology of this research session
docs/service-manual-search.md Service-manual search status (living document)
firmware/                     Locally archived vendor firmware (git-ignored)
firmware/hello/               First custom RAM payload (source only)
docs/vendor/                  Locally archived service documentation (git-ignored)
tools/                        Small reproducible extraction/probing helpers
```

## Current emulator status

The R17.00.02 package matching the test radio is decrypted and extracted. The
standalone M\*CORE simulator now executes the real R17 host image:

- `tools/run-mcore-r17.cmd`
- `firmware/extracted/host-boot-r17.elf` (local, git-ignored)
- Host load `0x10210000`, end `0x10494A68`

The R17 host reaches RTOS initialization, the application callback at
`0x102183BC`, and the scheduler/idle loop without faulting. The callback builds
an object lookup table at `0x1201EA58` with IDs `93`, `118`-`121`, and `30`.

The boot code also builds the real **87-entry runtime task table** at
`0x1201E3D0`. Task 86 is the application callback; tasks 30-33 share entry
`0x103B9334`. The UI framework uses a 30-entry object table at `0x12020730`
(stride `0x10C`), but that table is empty in the simulator.

The UI object constructor is at `0x103B4604`; attempts to run its callers reach
`PC 0x0` with `r15=0`, a missing low-ROM call. The LCD therefore receives only
initialization/command traffic. The RAPP image schedules the UI tasks but does
not provide the low-ROM object/display state they require.

See `docs/EMULATOR_STATUS.md` for the current state and
`docs/host-r17.00.02.md` for the address map.

## Tooling notes

- `tools/decrypt_cvn.py` captures Depot's decrypted `filePackage` XML via Frida
  without a FLASHkey and blocks radio serial writes.
- `tools/flashzap/` is the local vendor FlashZap client; it is git-ignored.
- The vendor firmware, extractor outputs, reset captures, and tool binaries are
  kept local and are not redistributed.

## Highest-value next steps

1. Obtain a boot-ROM image, or a small application-RAM capture around
   `0x12000000`/`0x12020730`; this is the shortest path to the stock UI.
2. If no capture is available, reconstruct the low-ROM object/display contract
   and populate `0x12020730` with synthetic UI objects.
3. Re-run the full task table and verify LCD/UI output before attempting any
   hello-world firmware.
4. Decide the P25 voice-codec licensing path (DVSI IMBE/AMBE vs. receive-only
   experiments vs. an external Codec2 path).
