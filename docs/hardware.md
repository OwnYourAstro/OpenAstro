# XTS 2500 hardware notes

## 1. Product family

The XTS 2500 is a Motorola **ASTRO 25** portable, P25 Phase 1 capable, in
Model I / II / III form factors. Bands seen in the wild and in this archive:

| Band | Model family examples | Notes |
| --- | --- | --- |
| VHF 136–174 MHz | `H46KDF9PW6BN`, `H46KDF9PW6AN` | 5 W class; MURS/marine/amateur use common |
| UHF 380–470 MHz | `AZ489FT4865` filing | 4–5 W class |
| UHF 403–470 / 450–520 | various | Regional splits |
| 700/800 MHz 764–870 | `H46UCF9PW6BN`, `H46UCF9PW6AN` | 2.5–3 W class |
| 800 MHz 806–870 | `AZ489FT5816` filing | 3 W class |
| 896–901 / 935–940 | `AZ489FT5849` filing | 2.5–2.8 W class |

RF output is continuously variable down to very low power (FCC filings say
0.07 mW or 250 mW depending on the filing). Tuning/calibration is per-radio.

## 2. Service documentation

Two detailed service manuals are now archived locally in `docs/vendor/`:

| Document | Part number | Pages | Coverage |
| --- | --- | ---: | --- |
| ASTRO XTS 2500/2500I/2250/1500/2000/ATS 3000, MT 1500/PR 1500 **Detailed Service Manual** | `6816985H01-F` | 914 | XTS 2500 family: theory, block diagrams, pinouts, test points, schematics, board overlays, parts lists |
| ASTRO XTS 5000 VHF/UHF1/UHF2/700–800 **Detailed Service Manual** | `6881094C31-E` | 374 | XTS 5000: same generation; useful comparison and memory/Patriot detail |

The XTS 2500 **Basic Service Manual** `6816984H01` is referenced by the detailed
manual for level 1/2 maintenance and pass/fail troubleshooting, but the detailed
manual itself contains the schematics, board overlays, and parts lists needed
for emulation and reverse engineering.

Key XTS 2500 manual sections:

| Section | Content |
| --- | --- |
| 4.1.6 / 4.2.6 / 4.3.6 / 4.4.6 / 4.5.6 | VOCON theory for VHF/UHF1/UHF2/700-800/900 |
| 4.x.6.1.1 | Patriot IC U800 |
| 4.x.6.1.2 | SRAM U804 |
| 4.x.6.1.3 | Flash U803 |
| 4.x.6.2.1 | MAKO IC U701 |
| 4.x.6.3.4 | display and keypad modules |
| 4.x.6.3.5 | encryption module |
| Chapter 7 | test points and voltages |
| Chapter 8 | U800/U803/U804/U701 pinouts |
| Chapter 9 | schematics, board overlays, parts lists |

## 3. Logic architecture

### 3.1 "Patriot" IC (U800) — confirmed

The XTS 2500 Detailed Service Manual (6816985H01-F, section 4.1.6.1.1) states:

- U800 is a **dual-core processor** with a **32-bit microcontroller unit
  (MCU)** and a **16-bit digital signal processor (DSP)** in one package.
- **256-pin BGA, 1 mm pitch**.
- Supplies: **1.875 V** core/EIM (E801) and **2.9 V** I/O (E800).
- Two clocks: **16.8 MHz sine (`CKIH`)** and **32.768 kHz square (`CKIL`)**.
  The 16.8 MHz clock generates the MCU/DSP clocks and most peripherals; the
  32.768 kHz clock is needed for reset and RTC-related logic.
- The MCU is described as **MCORE-based** in the XTL 5000 manual; the FlashZap
  RAM downloader confirms the ISA is **Motorola M\*CORE** (see
  [firmware.md](firmware.md)).

### 3.2 MCU

- **22.5K × 32 bits internal RAM**
- **1K × 32 bits internal ROM** for bootstrapping
- **External Interface Module (EIM):**
  - 24 external address lines
  - 16 bi-directional data lines
  - 6 chip selects
  - read/write and output enable
  - 1.8 V logic, runs at MCU clock speed
- **Multiple Queue SPI (MQSPI):** two independent SPI buses, 10 chip selects
  - SPI A: RF board (PCIC/FRACN on SPICS4, ABACUS III on SPICS5)
  - SPI B: VOCON devices (MAKO U701 on SPICS2 on the XTS 2500)
- **Two UARTs:** UART1 is the RS-232/side-connector UART, with RTS/CTS. On the
  XTS 2500 UART2 is unused; on the XTS 5000 UART2 is the SB9600 interface.
- **One-Wire interface** (Dallas/Maxim) for smart battery/cable detection.
- **MCU/DSP Interface (MDI)** internal to the Patriot.

### 3.3 DSP

- **84K × 24 bits program RAM**
- **62K × 16 bits data RAM**
- **Baseband Interface Port (BBP):** serial synchronous interface to the RF
  board; separate RX and TX data/clock/frame-sync.
- **DSP Timer module**
- **Serial Audio Codec Port (SAP):** 4-wire audio interface to the MAKO codec
  (512 kHz clock / 8 kHz frame sync on the XTS 2500).
- Shares USB and GPIO with the MCU.

The exact DSP core/ISA is still not proven. The manual only calls it a
"16-bit DSP". Do not assume DSP56300 without evidence.

### 3.4 Address/chip-select map (partial)

From the text and XTS 5000 "Patriot EIM and Memory Block Diagram":

| EIM signal | Device | Notes |
| --- | --- | --- |
| `CS0_N` | Flash U803/U402 | Flash `A(23:1)`, `D(15:0)` |
| `CS2_N` | SRAM U804/U403 | SRAM `A(19:1)`, `D(15:0)` |
| Display chip select | LCD module | XTS 2500 uses EIM `D0–D7`, write-only, address 0 |
| `CS4_N` | RF/other | Available chip select |
| `LBA_N` / `ADV` | Flash address valid | |
| `EB0_N` / `EB1_N` | Byte enables | Upper/lower byte |
| `OE_N`, `RW_N` | Flash/SRAM control | |

The **absolute base address of each chip select is not stated** in the service
manual. It must come from the boot code, the host image, or a logic capture.
This is a P0/P1 gap for the emulator.

The U800 pinout also lists `BOOT*` (F2) and `HAB_MOD` (A8), both marked "not
accessible on main board". These look like boot-mode/configuration straps and
should be investigated for a recovery/boot ROM entry path.

## 4. Memory devices

### 4.1 SRAM (U804)

- Asynchronous **1 MB** CMOS SRAM, **70 ns**, 1.8 V.
- 19 address lines, 16 data lines.
- `CS2_N` from the EIM; `EN_WE` = EIM R/W; `EN_OE` = EIM OE.
- Byte enables: `EN_BLE` = `EB1_N`, `EN_BHE` = `EB0_N`.
- Parts seen: `5185941F03` (8M, 512K×16, 70 ns, W18-compliant),
  `5171897M01` (8M, 512K×16, 55 ns) on later kits.

### 4.2 Flash (U803)

- Manual text for the early XTS 2500: **8 MB CMOS flash**, 70 ns, 1.8 V,
  22 address lines, 16 data lines.
- Contains **host firmware, DSP firmware, codeplug data, and tuning values**
  (the XTS 5000 stores tuning in a transceiver EEPROM; the XTS 2500 text says
  tuning values are in flash).
- `CS0_N` from the EIM; `ADV` = EIM `LBA`; `EN_WE` = EIM `EB1`; `EN_OE` = EIM
  `OE`; reset from Patriot `RESET_OUT` via a level translator.
- Parts lists show later kits with **64 MB** devices
  (`5185956E69`, `51012093001`, 60 ns, 1.8 V, 90 nm). Some entries label the
  part "DRAM", which conflicts with the theory text; treat the exact size as
  kit-dependent and verify against the board.
- The XTS 5000 has both an 8 MB flash part (`5199485A01`, burst) and a 64 MB
  part (`5185956E15`, 1.8 V, 60 ns) depending on the VOCON kit.

### 4.3 Boot ROM

The Patriot MCU contains a small **1K × 32 internal ROM** used for bootstrapping.
The external flash is the firmware store. The boot ROM's behaviour, entry
address, and whether it verifies the external image are still unknown.

## 5. Partition model (codeplug view)

The codeplug/RCMP view uses partition numbers, not physical addresses:

| Partition | Access | Meaning |
| --- | --- | --- |
| `0x80` | Read/write | Customer codeplug: zones, channels, personalities, scan, controls |
| `0x81` | Read/write locked | Security/EEPROM: serial `0x1004`, feature bitmask `0x1005`, FLASHcode `0x1006` |
| `0x82` | Read-only / tuning | RF calibration soft-pots. **Never write.** |
| `0x85` | Read/write locked | Two CPS block types; purpose not fully proven |

`0x83` is sometimes listed as host/DSP firmware in secondary write-ups; this is
**[U]** and should not be repeated as fact. Firmware is reached through
FlashZap/IROM/boot mode, not ordinary codeplug writes.

## 6. Audio, power, and support: MAKO IC (U701)

- **176-pin BGA, 0.8 mm pitch**, supplied from switched battery (`SW_B+`).
- Contains the VOCON power regulators: VSW1, VSW2, V_2.9, V1.55, V1.875, VCC5.
  The dual-core processor programs them over SPI B.
- **16-bit CODEC** with SAP interface to the DSP (512 kHz clock, 8 kHz frame
  sync); 24.576 MHz crystal for the audio clocks.
- Audio pre-amp, BTL audio power amp, filtering, multiplexing, internal/external
  mic and speaker paths.
- **10-bit ADC** with 8 general channels + 2 voltage monitors: display
  backlight button, volume, two-position toggle, `OPT_SEL_IN`, board type ID,
  battery voltage.
- **USB transceiver** (12 Mbps) and side-connector interface.
- One-Wire option detect, watchdog, power-up/down sequencing.
- SPI B connection to the Patriot: clock E6, MOSI B6, MISO C6, CS D6.

## 7. Display and keypad

- **96 × 64 pixel LCD** module, not field-repairable.
- Model II: 3 × 2 keypad + navigation button.
- Model III: 3 × 6 keypad + navigation button.
- The Patriot MCU drives the display through:
  - EIM data `D0–D7`
  - display chip select
  - EIM write-only line
  - EIM address 0 (register select)
  - display reset
  - `BL_EN` GPIO for backlight
- Keypad is a **7 row × 3 column matrix = 18 keys**. Columns are open-drain
  outputs pulled low; rows have pull-ups and are scanned. `ROW0–ROW6` and
  `COL0–COL2` are Patriot GPIOs (U800 pins in the Chapter 8 table).
- Side connector also carries PTT, volume, two-position toggle, option select,
  and battery/cable detect.

## 8. Encryption module ("Armour")

- Optional module on secure models, connected to the VOCON board by a **40-pin
  connector** (J601 on the radio, J701 on the encryption board).
- Contains a custom microcontroller IC called **Armour** for the encryption
  algorithms.
- Keys are loaded through the universal side connector, **pin 34**, from a KVL.
- Up to **16 keys**; finite or 30-second key retention depending on codeplug.
- Host communicates over the **4-wire SSI** bus. A failure produces
  `ERROR 09/10` or `S03` on the display.
- Algorithm kits include ADP software, AES, DES/DES-XL/DES-OFB, multikey, and
  UCM variants (see manual Table 4.1-2).
- ADP software encryption is DSP-based; hardware UCM is required for AES/DES.

## 9. RF architecture

The XTS 2500 RF board is band-specific and uses:

- **ABACUS III** (AD9874-class) IF digitizing subsystem, providing SSI data to
  the DSP and the RX sampling/LO clocks.
- **PCIC** (power control IC) and **FRACN** (fractional-N synthesizer) on the
  RF SPI bus.
- **MAKO** for TX BBP clock/frame sync on the XTS 2500 (the XTS 5000 uses the
  DSP timer for this on some VOCON kits).
- Per-band PA, preselector, VCO/PLL, and directional coupler.
- The DSP performs IF filtering, discrimination, modulation, and voice/signaling
  processing.

The exact RF IC part numbers per band are in the Chapter 9 parts lists.

## 10. Board/kits seen in the manual

| Band | RF board / kit examples |
| --- | --- |
| VHF | `PMLD4303A/D`, `PMLD4264B/E` |
| UHF1 | `PMLE2537A/D/F/G` |
| UHF2 | `PMLE4427A/B` |
| 700/800 | `PMLF4040A/B/C/F` |
| 900 | `PMLF4036A/B` |

Controller parts:

| Ref | Part | Description |
| --- | --- | --- |
| U800 | `5185941F04` | IC, PATRIOT BRAVO, 1.2.2, 256 BGA |
| U803 | `5185956E69` / `51012093001` | 64 MB, 60 ns, 1.8 V (later kits; manual text says 8 MB flash) |
| U804 | `5185941F03` / `5171897M01` | 8M SRAM, 512K×16, 70/55 ns |
| U701 | `5185143E77` | MAKO ASIC, CMOS power/audio |
| U201 | `5116245H01` / `5185941F40` | LVFRACN / 12-bit DAC (varies) |

The XTS 5000 uses the same Patriot concept with `U401` (Patriot Bravo),
`U402` flash, `U403` SRAM, `U501` MAKO/GCAP, and `U500` ABACUS III. This makes
the XTS 5000 manual a useful second source for the family architecture, but the
board/kits and some clock/USB paths differ.

## 11. FCC evidence

Public filings (internal photos, operational descriptions, some schematics):

| FCC ID | Band | Notes |
| --- | --- | --- |
| `AZ489FT5816` | 806–870 MHz | XTS2500 original; internal photos and operational description public |
| `AZ489FT5804` | 764–870 MHz | 700/800 XTS2500; multiple Class II changes |
| `AZ489FT3807` | 136–174 MHz | VHF XTS2500 |
| `AZ489FT4865` | 380–470 MHz | UHF XTS2500 |
| `AZ489FT5849` | 896–901 / 935–940 MHz | 900 MHz variant |

The internal photos show a shielded RF section and a digital section with two
large BGA packages plus smaller devices, consistent with the Patriot + flash +
SRAM design. The service-manual schematics are now the better source.

## 12. What this means for OpenAstro

- **Protocol emulator:** no hardware modelling needed beyond AT/PPP/RCMP,
  codeplug state, tuning state, display, and keypad.
- **Full firmware emulator:** model M\*CORE, the EIM, flash/SRAM, UART/USB,
  SPI/SSI, LCD, keypad, MAKO codec/power, and (for voice) the DSP.
- **Open firmware:** M\*CORE GCC is available; the missing pieces are the
  absolute memory map, boot ROM/signature behaviour, and DSP ISA.
