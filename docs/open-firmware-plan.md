# Open-source firmware plan for the XTS 2500

This is a research plan, not a claim that unsigned firmware will boot. The
first task is to learn what the boot chain will accept.

## 1. What "open firmware" can mean

| Level | Scope | Difficulty |
| --- | --- | --- |
| L0 | Host-side tooling / codeplug / emulator | Low; already partially done |
| L1 | A test program loaded into RAM through FlashZap | Medium; needs M\*CORE toolchain + flash/UART model |
| L2 | Replacement host application in flash (UI, codeplug, AT, scanning) | High; needs boot chain and peripherals |
| L3 | DSP/modem replacement (P25 waveform, vocoder, audio) | Very high; DSP ISA + patents |
| L4 | Full radio replacement including RF calibration/alignment | Extreme; needs service monitor and factory data |

A realistic project starts at L1/L2 and treats L3/L4 as research.

## 2. Legal and ethical constraints

- Do not redistribute Motorola firmware, service software, or entitlement
  material.
- Do not use this work to operate on systems without authorization.
- The P25 voice codec is patented by DVSI (IMBE for Phase 1, AMBE+2 for Phase
  2/DMR). A clean-room implementation still needs a licensing decision. This is
  not legal advice; get a real opinion before shipping a codec.
- Keep radios you experiment on off live systems. Test into a dummy load or
  attenuator.
- RF calibration (`0x82`) is per-radio. Losing it requires a service monitor
  and the alignment procedure. Back it up before any flash work if possible.

Possible voice paths:

1. License or use a DVSI chip/module for IMBE/AMBE.
2. Receive-only experimental decoder for research (still patent-sensitive).
3. Use an external open codec/modem (Codec2/M17) over the radio's audio path
   for non-P25 modes; this does not make the radio P25-compatible.
4. Partner with a project that already has a licensed codec.

## 3. Toolchain

### 3.1 Host CPU (M\*CORE)

- GCC still contains `gcc/config/mcore/` (M\*CORE machine description,
  big/little endian, M210/M340).
- Binutils has `mcore-elf` targets and a disassembler.
- GDB has `sim/mcore` (instruction interpreter and debugger).

Work items:

- Build a reproducible `mcore-elf` GCC/binutils/newlib toolchain.
- Determine the exact Patriot M\*CORE variant and endianness.
- Write startup code, linker script, and a RAM/ROM image layout.
- Validate against the vendor RAM downloader (same ISA, known behaviour).

### 3.2 DSP

Unknown. Options:

- identify the DSP core from the service manual or DSP image;
- check whether a public toolchain exists (Motorola DSP56k, StarCore, etc.);
- if proprietary, treat the DSP as a black box at first and keep the vendor
  DSP image; replace only the host application.

## 4. Boot and flash path

The factory path, from FlashZap:

```
SBEP/RCMP session
  → unlock / boot mode
  → load RAM downloader into RAM
  → erase/program flash from S-records
  → write flash markers / PSDT
  → reset into host application
```

Questions that decide the project:

1. Does the boot application verify a signature/MAC on the host image?
2. Does it require a PSDT or model/serial match?
3. Can the RAM downloader be loaded on an unlocked radio without vendor
   authorization?
4. Where are the flash markers, and what do they protect?
5. Is there a recovery mode that always accepts a known-good image?

If unsigned host images are accepted, L2 is feasible. If not, the project must
either find a legitimate signing path or replace the boot chain, which is much
riskier.

## 5. Minimum viable custom firmware

Start with a host application that does not need the DSP or RF:

- boot and initialise clocks, RAM, flash, watchdog;
- UART/USB console and AT identity;
- read the codeplug from flash and expose it over RCMP;
- drive the LCD and scan the keypad;
- implement channel/zone selection and display;
- log received RF telemetry without transmitting.

Then add:

- audio path and codec;
- RF synthesizer control and tuning data access (read-only at first);
- P25 receive (needs DSP);
- P25 transmit (needs DSP, calibration, and regulatory care).

## 6. Phased plan

| Phase | Goal | Exit criteria |
| --- | --- | --- |
| P0 | Toolchain and RAM downloader | Build an M\*CORE image that prints on a real radio via FlashZap |
| P1 | Persistent test loader | Load/flash a minimal image that survives reset |
| P2 | Host bring-up | Display, keypad, UART/USB, watchdog, flash |
| P3 | Codeplug + AT | Read/write codeplug; AT identity; no RF |
| P4 | RF control | Synthesizer, tuning reads, RSSI; receive-only |
| P5 | DSP integration | Keep vendor DSP, control it from the host; or replace it |
| P6 | Voice | Licensed IMBE/AMBE path or external codec |
| P7 | Transmit | Calibrated, legal, bench-tested transmit |

## 7. Risks

- Bricking the radio or erasing calibration.
- Signed/secure boot blocks custom images.
- Unknown DSP ISA and proprietary firmware.
- RF/PA/filter limits and regulatory compliance.
- Patent licensing for voice.
- Model/band differences in flash layout and peripherals.
- Vendor tooling dependencies (Windows, dongles, activation) for recovery.

## 8. Immediate experiments

1. Build `mcore-elf` GCC/binutils/newlib and reproduce the RAM downloader.
2. Use FlashZap on a bench radio to load a "hello world" RAM downloader.
3. Capture the SBEP/RCMP traffic and document the boot-mode handshake.
4. Dump/decrypt one `.cvn` host image and locate its entry point.
5. Use the service-manual pinouts/schematics to map every IC and test point
   on the actual board, then recover the absolute EIM chip-select addresses.
