# XTS 2500 emulator plan

Current runtime status, observations, and the missing boot-ROM/application-RAM
state are recorded in [EMULATOR_STATUS.md](EMULATOR_STATUS.md).

There are two useful emulator products. Build them separately.

## A. Protocol/device emulator (achievable now)

A virtual radio that speaks the **outside** of the radio:

- USB CDC-ACM / PTY / TCP endpoint.
- AT command set (`AT`, `AT&V`, `AT#DATLCL=1`, `AT+IPR`, `CLIENT`, `ATD`).
- PPP (LCP/IPCP), optional TCP `192.168.128.1:8002`.
- RCMP read/write/prepare/session/auth.
- Codeplug state loaded from a `.cpg` or synthetic JSON.
- Partition policy: `0x80`/`0x81` writable, `0x82` read-only, firmware
  partitions inaccessible.
- Tuning state loaded from `.tun`, with soft-pot reads and a hard write block.
- A simple logical keypad/LCD model so tools can exercise button/display paths.

This is enough to develop and regression-test CPS/OpenAstro tooling without
risking a radio, and to replay captured sessions.

Building blocks already exist:

- A standalone virtual-radio RCMP server was written in the independent
  `open-astro-cps` project and covers read/write/session/auth plus a `0x82`
  firewall.
- The codeplug reader/writer and RCMP transport in this project's prior work
  already model the real records and CRC.
- Captured sessions and codeplug fixtures provide golden inputs.

Recommended implementation: a small C++/Python service with a pluggable
transport, deterministic time, scriptable keypad, and a JSON session log.
Emulate at the message level, not the wire level, then add a wire adapter.

## B. Full firmware emulator (hard, but feasible)

Goal: execute the real host application (and eventually DSP) with emulated
hardware, render the LCD, inject key presses, and observe the firmware.

### B.1 CPU

The host is Motorola **M\*CORE** (confirmed for the FlashZap RAM downloader,
strongly indicated for the host application). There is no M\*CORE target in
QEMU or Unicorn today. Options:

1. **Port GDB's `sim/mcore` interpreter** into a standalone library. It already
   implements the instruction set and is the cheapest path to correctness.
2. **Write a fresh M\*CORE interpreter** from the binutils opcode table and the
   M\*CORE manual; add a decoded-instruction cache for speed.
3. **Add an M\*CORE target to QEMU.** Most work, best long-term performance and
   debugging integration.
4. **Use a vendor/legacy simulator** if one can be found; verify licensing.

Start with (1) to boot the RAM downloader, then decide whether performance
requires (3).

### B.2 Memory map and boot

Known from the XTS 2500 Detailed Service Manual:

- Patriot U800: 256-pin BGA, 32-bit MCU + 16-bit DSP; 1.875 V core/EIM,
  2.9 V I/O; 16.8 MHz `CKIH`, 32.768 kHz `CKIL`.
- MCU: 22.5K×32 internal RAM, 1K×32 internal boot ROM, EIM with 24 address
  lines, 16 data lines, 6 chip selects.
- Flash U803 on `CS0_N`; SRAM U804 on `CS2_N`; display on its own EIM CS.
- UART1 (RS-232/side connector) and UART2 (unused on XTS 2500, SB9600 on
  XTS 5000); two SPI buses/10 chip selects; one-wire; GPIO.
- DSP: 84K×24 program RAM, 62K×16 data RAM, BBP, DSP timer, SAP; MDI to MCU.

Still needed:

- **absolute base address of each chip select**;
- boot ROM entry/behaviour and reset vector;
- host/DSP image load addresses and the handoff;
- vector table and exception model;
- flash command set and markers;
- interrupt/timer register map;
- clock/reset controller.

Until then, use the RAM downloader as the first target: it is a small,
self-contained M\*CORE program with known load/entry addresses (
`0x00100400` / `0x00100500`) and a UART/USB console. A correct CPU plus a
minimal UART should print `Ready to Program`.

### B.3 Peripherals (in priority order)

1. **UART / USB CDC-ACM / SBEP**: boot messages, AT, RCMP. USB transceiver is
   inside MAKO U701; UART1 is on the Patriot.
2. **Flash controller**: U803 on EIM `CS0_N`; identify, erase, program, protect,
   markers. Exact part/size is kit-dependent (8 MB early / 64 MB later).
3. **Timers / interrupt controller**: scheduler and timebase.
4. **GPIO / keypad / rotary knob**: 7×3 keypad matrix, side controls, knob.
5. **LCD controller**: 96×64, EIM `D0–D7`, CS, write, address 0.
6. **SPI / SSI**: MAKO U701 (SPI B), PCIC/FRACN/ABACUS III (SPI A), EEPOTs,
   DSP interface (MDI), BBP and SAP.
7. **Audio codec**: MAKO 16-bit CODEC, 512 kHz/8 kHz SAP.
8. **DSP core + ISH loader**: only needed for P25/voice.
9. **UCM / keyfill**: Armour module on 40-pin connector, SSI, keyfill pin 34.
10. **RF synthesizer/PA telemetry**: needed for realistic tuning/RSSI.

### B.4 Firmware images

The emulator needs at least the host application. Sources, best first:

- **FlashZap Read Memory** dump of U803 from a bench radio (S-records);
- capture a CPS/Depot firmware update and reconstruct the decrypted S-records;
- decrypt/extract `.cvn` (see [firmware.md](firmware.md));
- read the flash chip physically;
- use a RAM downloader or small test S-record for early CPU work.

Keep vendor images out of git.

### B.5 Milestones

| Milestone | Pass condition |
| --- | --- |
| M0 CPU | M\*CORE executes the RAM downloader and reaches its command loop |
| M1 Console | Emulated UART/USB prints `FlashZap Downloader` / `Ready to Program` |
| M2 Flash | Emulated W18-B flash identifies, erases, programs an S-record |
| M3 Host boot | Host image boots far enough to initialise display and AT |
| M4 Identity | `AT&V` returns model/serial/firmware strings from emulated state |
| M5 Codeplug | RCMP read returns a valid `.cpg`; write updates state |
| M6 UI | Keypad + LCD show the home screen and channel changes |
| M7 DSP | DSP image boots and passes its self-test |
| M8 Voice | P25 receive/transmit audio path works (licensing permitting) |

### B.6 Testing

- Golden AT transcripts and RCMP captures from real hardware.
- Codeplug fixtures with known CRCs and directory entries.
- Deterministic instruction traces for the RAM downloader.
- Screen snapshots at defined key sequences.
- Fault injection on flash/erase and transport timeouts.

### B.7 Risks

- M\*CORE documentation and tooling are old; validation against real code is
  essential.
- The DSP may be a custom core with no public ISA documentation.
- Secure boot/signature checks may prevent running modified host images.
- RF/calibration behaviour cannot be validated without hardware and a service
  monitor.
- P25 voice needs DVSI IMBE/AMBE; a clean-room decoder is a separate legal and
  engineering project.
