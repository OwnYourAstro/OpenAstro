# Service manual review

Two detailed service manuals were reviewed. They are vendor documents kept
locally in `docs/vendor/` and are git-ignored.

## 1. XTS 2500 Detailed Service Manual

**File:** `docs/vendor/XTS2500_XTS1500_MT1500_PR1500_Detailed_Service_Manual_6816985H01-F.pdf`

- Part number: `6816985H01-F`
- Date: February 14, 2012
- Pages: 914
- Covers: XTS 2500 / 2500I / 2250 / 1500 / 2000 / ATS 3000, MT 1500, PR 1500.

### Structure

| Chapter | Topic |
| --- | --- |
| 1 | Introduction / model charts |
| 2 | Theory of operation (RF, control, power) |
| 3 | Power distribution and DC paths |
| 4.1–4.5 | Detailed VOCON theory by band: VHF, UHF1, UHF2, 700/800, 900 |
| 5–6 | Troubleshooting |
| 7 | Test points and voltages |
| 8 | Pinout tables: flash U803, SRAM U804, Patriot U800, MAKO U701 |
| 9.1–9.5 | Schematics, board overlays, parts lists by band |

### Key findings (verified from the text)

- **U800 Patriot**: 256-pin BGA, 1 mm pitch, 32-bit MCU + 16-bit DSP, 1.875 V
  core/EIM, 2.9 V I/O.
- **Clocks**: 16.8 MHz `CKIH` and 32.768 kHz `CKIL`; 16.8 MHz is internally
  divided to run the MCU, DSP, and peripherals.
- **MCU**: 22.5K×32 internal RAM, 1K×32 internal ROM for bootstrapping; EIM with
  24 address lines, 16 data lines, 6 chip selects; two SPI buses/10 chip
  selects; two UARTs (UART1 RS-232, UART2 unused); one-wire; MDI.
- **DSP**: 84K×24 program RAM, 62K×16 data RAM; BBP, DSP timer, SAP; shares USB
  and GPIO with the MCU.
- **SRAM U804**: 1 MB, 70 ns, 1.8 V, 19 address lines, 16 data lines, EIM
  `CS2_N`.
- **Flash U803**: EIM `CS0_N`, 22 address lines, 16 data lines, 1.8 V. Theory
  text says 8 MB and lists host firmware, DSP firmware, codeplug, and tuning
  values. Later parts lists show 64 MB devices.
- **MAKO U701**: 176-pin BGA, 0.8 mm; all VOCON regulators; 16-bit CODEC;
  audio pre-amp/PA; 10-bit ADC; USB transceiver; watchdog; one-wire; side
  connector; SPI B to Patriot.
- **Display**: 96×64 LCD; EIM `D0–D7`, display CS, write-only, address 0,
  reset; `BL_EN` backlight. Model II 3×2 + nav; Model III 3×6 + nav.
- **Keypad**: 7 rows × 3 columns = 18 keys; open-drain columns, pulled-up rows,
  scanned by the MCU.
- **Encryption module**: "Armour" custom MCU, 40-pin connector, SSI to host,
  keyfill on side-connector pin 34, up to 16 keys.
- **RF**: ABACUS III IF digitizer, PCIC/FRACN on RF SPI, MAKO TX BBP clocks,
  per-band PA/filter/synthesizer.
- **Parts**: U800 `5185941F04` (Patriot Bravo 1.2.2, 256 BGA), U804
  `5185941F03` / `5171897M01` (8M SRAM), U803 `5185956E69` / `51012093001`
  (64 MB parts), U701 `5185143E77` (MAKO).

### Discrepancies / cautions

- The theory text says **8 MB flash**, while later parts lists show **64 MB**
  and sometimes label the part "DRAM". Treat the size as **kit-dependent** and
  verify the actual board.
- The manual does not name the MCU ISA or the DSP core. The **M\*CORE** result
  comes from the FlashZap RAM downloader, not this manual.
- Absolute EIM base addresses and boot-ROM code are **not** published.

## 2. XTS 5000 Detailed Service Manual

**File:** `docs/vendor/XTS5000_Detailed_Service_Manual_6881094C31-E.pdf`

- Part number: `6881094C31-E`
- Date: November 16, 2006 (updated 2011)
- Pages: 374
- Covers: XTS 5000 VHF, UHF Range 1, UHF Range 2, 700–800 MHz.

### Key findings

- Same Patriot concept: `U401` (256-pin BGA, 32-bit MCU + 16-bit DSP),
  `U402` flash, `U403` SRAM, `U501` MAKO/GCAP II, `U500` ABACUS III (AD9874).
- MCU: 22.5K×32 RAM, 1K×32 boot ROM, EIM 24 address/16 data/6 CS, two SPI
  buses/10 CS, two UARTs (UART2 is SB9600 on XTS 5000), one-wire, MDI.
- DSP: 84K×24 program RAM, 62K×16 data RAM, BBP, DSP timer, SAP.
- “Patriot EIM and Memory Block Diagram” (manual page 3-23) shows flash on
  `CS0_N` with `A(23:1)`, SRAM on `CS2_N` with `A(19:1)`, and byte enables.
- Board kits differ: NTN9564, NNTN4563, NNTN4819, NNTN4717, NNTN5567. Some use
  GCAP II, some MAKO; some generate SAP on the DSP, some on MAKO/Flipper.
- Flash parts: 8 MB burst (`5199485A01`) and 64 MB (`5185956E15`) variants.
- SRAM `5185368C82` / `5185941F03` (1 MB class).
- Tuning values live in a transceiver-board serial EEPROM on XTS 5000, whereas
  the XTS 2500 text says tuning values are in flash. Confirm per model before
  assuming a location.

### Useful differences vs XTS 2500

| Item | XTS 2500 | XTS 5000 |
| --- | --- | --- |
| Patriot ref | U800 | U401 |
| Flash / SRAM | U803 / U804 | U402 / U403 |
| Audio/power | MAKO U701 | GCAP II or MAKO U501 |
| UART2 | unused | SB9600 |
| Display bus | EIM `D0–D7` | EIM on some kits, SPI on others |
| Tuning | flash (text) | transceiver EEPROM |

## 3. What to extract next from the manuals

1. Render and trace the Patriot U800/U401 schematic at high resolution.
2. Transcribe the complete U800 pinout (Chapter 8 tables) into a machine-readable
   file: pin, signal, direction, peripheral, test point.
3. Map the flash/SRAM address/data/control nets to the EIM pin numbers.
4. Extract the display/keypad connector pinouts and the encryption connector.
5. Extract the test-point table (Chapter 7) for hardware bring-up and for
   emulator I/O naming.
6. Record the parts list for each band/kit and resolve the 8 MB vs 64 MB flash
   question by board revision.
7. Look for any boot-mode strap (e.g. `BOOT*`, `HAB_MOD`) and its default.
