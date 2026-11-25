# Firmware archive manifest

Vendor files archived locally for interoperability research. **Do not commit
or redistribute.** Hashes are also in `SHA256SUMS.txt`.

## XTS 2500

| File | Bytes | Notes |
| --- | ---: | --- |
| `XTS2500_DVN4228S.cvn` | 14,788,821 | `.cvn` FLASHport package, 2011 header |
| `XTS2500_DVN4228W.cvn` | 16,876,691 | `.cvn`, from Desktop |
| `XTS2500_DVN4228Y.cvn` | 16,883,539 | `.cvn`, 2012 header |
| `XTS2500_DVN4301B.cvn` | 17,028,618 | `.cvn`, from Desktop |
| `XTS2500_DVN4301J_R20.50.09.cvn` | 17,301,351 | `.cvn`, 2016 header; R20.50.09 |
| `XTS2500_R09.00.03_DVN4136M.zip` | 7,442,383 | ZIP containing one `.cvn` |
| `XTS2500_R09.00.05.zip` | 7,444,564 | ZIP containing one `.cvn` |

## XTS 5000 (for comparison)

| File | Bytes | Notes |
| --- | ---: | --- |
| `XTS5000_DVN4225Y.cvn` | 8,432,597 | `.cvn` |
| `XTS5000_DVN4274G 19.5.cvn` | 9,613,959 | `.cvn`, 2013 header |
| `XTS5000_DVN4274P_R20.50.09.cvn` | 9,886,691 | `.cvn`, 2016 header |
| `XTS5000_R09.00.05_DVN4109S.zip` | 7,444,501 | ZIP containing one `.cvn` |
| `XTS5000_R15.00.00_DVN4225N.zip` | 8,369,793 | ZIP containing one `.cvn` |

## Tools

| File | Bytes | Notes |
| --- | ---: | --- |
| `astro25_flashzap_for_astro25_radios_admin_admin.rar` | 5,717,803 | FLASHZap client R01.28.00, Patriot/OMAP RAM downloaders, docs |

## Vendor documentation

| File | Bytes | Notes |
| --- | ---: | --- |
| `../docs/vendor/XTS2500_XTS1500_MT1500_PR1500_Detailed_Service_Manual_6816985H01-F.pdf` | 76,696,093 | XTS 2500/2500I/2250/1500/2000/ATS3000/MT1500/PR1500 Detailed Service Manual, 914 pages |
| `../docs/vendor/XTS5000_Detailed_Service_Manual_6881094C31-E.pdf` | 21,311,656 | XTS 5000 VHF/UHF1/UHF2/700–800 Detailed Service Manual, 374 pages |
| `../docs/vendor/astro_xtl_5000_sm.zip` | 7,208,358 | XTL 5000 Basic Service Manual 6881096C73-O (PDF) |

## Extracted analysis artifacts

`extracted/` is for derived, non-vendor files (S-record conversions, manifests,
hashes). Do not place decrypted vendor images there if they would be committed;
add specific ignore rules if needed.

## Licence / provenance

These files were copied from the machine owner's Windows profile as part of a
right-to-repair/interoperability research effort. They remain the property of
their respective owners. Keep them local, do not publish them, and do not use
them to operate radio systems without authorization.

## Decrypted analysis artifacts (local only)

Generated on 2026-11-24 from
`XTS2500_DVN4301J_R20.50.09.cvn` after Depot unwrapped the file package:

| Artifact | Bytes |
| --- | ---: |
| `extracted/XTS2500_R20.50.09.decrypted.xml` | 34,602,556 |
| `extracted/package/RAPP-R20.50.09-H46.......BN.srec` | 7,817,936 |
| `extracted/XTS2500_R20.50.09_RAPP.bin` | 2,791,612 |
| `extracted/XTS2500_R19.50.01_DSP2.bin` | 327,680 |
| `extracted/XTS2500_R19.50.01_DSPB.bin` | 327,680 |
| `extracted/XTS2500_R07.11.12_CFWI.bin` | 309,118 |

These remain under the git-ignored `firmware/extracted/` tree. They are
derived vendor images and must not be redistributed.