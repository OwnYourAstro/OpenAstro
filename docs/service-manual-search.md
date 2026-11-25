# XTS 2500 service manual search

## Status: found

Two detailed service manuals were supplied and are archived in `docs/vendor/`:

| Document | Part number | Pages | Bytes |
| --- | --- | ---: | ---: |
| ASTRO XTS 2500/2500I/2250/1500/2000/ATS 3000, MT 1500/PR 1500 **Detailed Service Manual** | `6816985H01-F` | 914 | 76,696,093 |
| ASTRO XTS 5000 VHF/UHF1/UHF2/700–800 **Detailed Service Manual** | `6881094C31-E` | 374 | 21,311,656 |

Hashes are in `firmware/SHA256SUMS.txt`.

- [x] Located complete copies
- [x] Verified XTS 2500 coverage
- [x] Extracted controller/RF theory, pinouts, schematics, parts lists
- [x] Identified Patriot, flash, SRAM, MAKO, display/keypad, encryption module

## What the XTS 2500 manual gives us

- Patriot U800 theory: 32-bit MCU + 16-bit DSP, clocks, EIM, SPI, UART,
  one-wire, USB, GPIO, MDI, DSP RAM/BBP/SAP.
- SRAM U804 and flash U803 bus/chip-select wiring and sizes.
- MAKO U701: regulators, CODEC, audio, ADC, USB transceiver, watchdog.
- Display (96×64, EIM D0–D7/CS/write/address 0) and 7×3 keypad matrix.
- Encryption module "Armour": 40-pin connector, SSI, keyfill pin 34, 16 keys.
- Chapter 7 test points, Chapter 8 pinouts, Chapter 9 schematics/overlays/parts.
- Grid of RF boards by band: PMLD4303/4264 (VHF), PMLE2537 (UHF1),
  PMLE4427 (UHF2), PMLF4040 (700/800), PMLF4036 (900).

## Still not found

- **Basic Service Manual `6816984H01`** — referenced for level 1/2
  troubleshooting and pass/fail servicing. Not needed for the emulator or
  firmware analysis, but useful for repair/recovery procedures.
- **Absolute EIM base addresses / boot ROM** — not published in the service
  manual. Must come from firmware, boot code, or a logic capture.
- **DSP core documentation** — the manual says "16-bit DSP" but does not name
  the core or ISA.

## Next places to search (lower priority)

1. Basic Service Manual `6816984H01` (archive.org, manuals sites, repair
   forums, paper/CD copies).
2. Motorola depot/service training material for the ASTRO 25 portable.
3. Board photographs with readable chip markings for each band/kit.
4. FCC exhibits for any later XTS 2500 variants not covered by the current
   filings.

## Search hygiene

For any new candidate, record filename, size, SHA-256, source/provenance,
model/revision coverage, whether schematics/parts lists are included, and
redistribution status. Keep vendor documents local and git-ignored.
