# Knowledge gaps

Prioritised by what blocks the emulator and open firmware. "Close by" is the
cheapest credible path.

## P0 — blocks both projects

### G1. Absolute EIM base addresses, boot ROM, and reset vectors
**Missing:** the physical base address of each EIM chip select, the boot ROM
entry/behaviour, the reset vector, and whether the boot ROM verifies the image.

**Why:** the **XTS 2500 Detailed Service Manual** (`6816985H01-F`) is now in
`docs/vendor/` and supplies the schematics, board overlays, chip part numbers,
pinouts, test points, clock tree, and power rails. It does **not** publish the
absolute memory map or boot-ROM code. Without those, the emulator can model the
devices but cannot boot the firmware.

**Close by:** analyze a host image or boot dump, capture the first bus cycles
with a logic analyzer, or find the boot ROM in a flash dump. The Basic Service
Manual `6816984H01` is still useful for level 1/2 troubleshooting but is not the
critical missing piece any more.

### G2. Decrypt/extract `.cvn` firmware
**Missing:** host and DSP images in analysable form.

**Why:** without code there is no emulator target and no reference for open
firmware.

**Close by (best first):**
- **FlashZap Read Memory** (`readMemory` / `readmem.srec`) to dump U803 from a
  bench radio as S-records — bypasses `.cvn` entirely;
- capture a CPS/Depot FLASHport update on Windows and extract the S-records
  after the tool decrypts them;
- reverse the `.cvn` reader in the CPS/Depot DLLs;
- dump flash physically if the bootloader read range is restricted.

### G3. Patriot M\*CORE details
**Missing:** exact core variant, endianness, exception model, MMU/MPU, cache,
timers, interrupt controller, and the absolute bus mapping.

**Why:** the CPU core can be emulated from `sim/mcore`, but the SoC around it
cannot. The manual gives the EIM/SRAM/flash/UART/SPI/GPIO structure and pin
numbers; it does not give register addresses.

**Close by:** use the RAM downloader as a CPU conformance test; extract the
host image and locate the vector table, chip-select setup, and interrupt
controller initialisation.

### G4. DSP core and image format
**Known:** 16-bit DSP, 84K×24 program RAM, 62K×16 data RAM, BBP, DSP timer, SAP,
MDI to the MCU (service manual).
**Missing:** DSP ISA, register map, `.ish` format, boot handoff, and the exact
DSP part/core.

**Why:** no P25 voice, modem, or DSP self-test without it.

**Close by:** DSP image extraction, logic-analyzer capture of the MDI/BBP/SAP
buses, service-manual schematic tracing, or reuse the vendor DSP image as a
black box.

### G5. Boot ROM / secure boot / signing
**Missing:** whether host/DSP images are signed or MACed, what the flash
markers/PSDT validate, and whether unsigned images will boot.

**Why:** determines whether open firmware is possible without replacing the
boot chain.

**Close by:** FlashZap/PSDT analysis, boot-mode captures, controlled image
modification on a recoverable radio.

## P1 — blocks a useful emulator

### G6. Flash controller and geometry
**Known:** U803 (XTS 2500) / U402 (XTS 5000) on EIM CS0; 22 address lines,
16 data lines, 1.8 V, 70 ns in early descriptions; 8 MB in theory text; later
parts lists show 64 MB devices (parts `5185956E69`, `51012093001`,
`5185956E15`). The RAM downloader mentions Intel W18-B 4/8/16 MB.
**Missing:** exact part and size per kit, sector map, command set, protection,
flash markers, and bad-block handling.

**Close by:** read the chip marking on the actual board; inspect the flash
command sequences in the host/RAM downloader; capture a FlashZap erase/program
session.

### G7. USB / UART / SBEP details
**Missing:** endpoint behaviour in boot mode, SBEP framing/checksums, buffer
sizes, timeouts, error recovery.

**Close by:** USB captures of FlashZap in normal and boot modes.

### G8. Display and keypad
**Known:** 96×64 LCD; Model II 3×2 + nav, Model III 3×6 + nav; EIM D0–D7,
display CS, write-only, address 0, reset, backlight; 7×3 keypad matrix (18
keys), open-drain columns and pulled-up rows; side controls and rotary knob
wiring in the service manual.
**Missing:** LCD controller command set and timing; exact rotary-knob encoding;
keypad membrane/backlight details.

**Close by:** firmware display driver traces, logic capture of the LCD bus, and
the schematic/board overlay.

### G9. Audio and RF peripherals
**Known:** MAKO U701 (16-bit CODEC, regulators, audio PA, 10-bit ADC, USB
transceiver, watchdog, one-wire, side connector); ABACUS III IF digitizer;
PCIC/FRACN on the RF SPI bus; encryption module "Armour" on the 40-pin
connector, SSI interface, keyfill pin 34.
**Missing:** register-level programming, exact RF IC variants per band, PA bias
and RSSI/EEPOT details, UCM protocol, and calibration semantics.

**Close by:** service manual schematics and parts lists, firmware SPI/SSI
traces, and a logic capture of the RF bus.

### G10. Emulator CPU performance
**Missing:** a fast M\*CORE implementation. GDB `sim/mcore` is correct but
slow; a decoded-cache interpreter or QEMU target may be needed for real-time
UI/audio.

## P2 — blocks a complete radio

### G11. P25 voice codec licensing
**Missing:** a legal IMBE/AMBE implementation or licensed hardware.

**Options:** DVSI license/chip, receive-only research, external Codec2/M17
(not P25-compatible), or partner with a licensed project.

### G12. Calibration and RF alignment
**Missing:** factory alignment procedure, soft-pot semantics, test limits,
service-monitor workflow.

**Why:** custom RF code without calibration can transmit off-frequency or
out-of-compliance. Never write `0x82` without a backup and a service monitor.

### G13. Model/band variants
**Missing:** differences between VHF/UHF/700-800/900, Model I/II/III, UCM/no
UCM, flash size, firmware branches.

**Close by:** collect codeplugs, service manuals, and board photos for each
variant; add model profiles to the emulator.

### G14. Keyfill / UCM
**Missing:** side-connector pinout, 3-wire protocol details, SLN/CKR mapping,
UCM firmware behaviour.

**Close by:** KFDtool documentation and a logic capture of a real keyfill.

## Things we do know (do not re-research)

- USB CDC-ACM `0cad:1001`, AT handshake, PPP, RCMP transport.
- Codeplug `.cpg` container, RCMP record shapes, CRC, auth LFSR, write/commit.
- Partition policy: `0x80` codeplug, `0x81` security, `0x82` tuning (never
  write), `0x85` locked.
- FLASHcode format and Q667 ADP bit.
- Firmware split: host S-record + DSP `.ish`.
- RAM downloader: M\*CORE big-endian, load `0x00100400`, entry `0x00100500`.
- Patriot U800: 256-pin BGA, 32-bit MCU + 16-bit DSP, 1.875 V core / 2.9 V I/O,
  16.8 MHz + 32.768 kHz clocks, 22.5K×32 MCU RAM + 1K×32 boot ROM, EIM
  24 addr/16 data/6 CS, two SPI buses/10 CS, two UARTs, one-wire, MDI; DSP
  84K×24 program RAM / 62K×16 data RAM, BBP/SAP.
- SRAM U804: 1 MB, 19 addr/16 data, CS2; Flash U803: EIM CS0, 8 MB early /
  64 MB later kits.
- MAKO U701: 176-pin BGA, regulators, 16-bit CODEC, audio PA, ADC, USB
  transceiver, watchdog, one-wire; SAP 512 kHz/8 kHz.
- Display/keypad: 96×64 LCD, EIM D0–D7 + CS + write + address 0; 7×3 keypad.
- Encryption module: Armour IC, 40-pin connector, SSI, keyfill pin 34, up to 16
  keys.
- Firmware versions and files listed in `firmware/MANIFEST.md`.
- Service manual files listed in `docs/vendor/` and hashed in
  `firmware/SHA256SUMS.txt`.
