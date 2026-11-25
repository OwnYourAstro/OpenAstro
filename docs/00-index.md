# Document map and evidence labels

Every factual claim should carry how it is known. Use these labels:

| Label | Meaning |
| --- | --- |
| **[V]** | Verified in this research session by inspecting a file, running a tool, or reading a measured capture |
| **[C]** | Verified by this project's prior clean-room codeplug work on a real XTS 2500 |
| **[H]** | Hardware-family evidence (service manual, FCC filing, vendor tool) that strongly applies, but has not been re-verified on the exact XTS 2500 unit |
| **[U]** | Unverified, plausible, or inferred — must be confirmed before relying on it |
| **[X]** | Known-wrong or contradicted; do not use |

Beware: `RivasMario/open-astro-cps` contains both excellent verified work and a
documented history of fabricated protocol notes. Its `docs/README.md` labels
the bad files. This archive only reuses material from that repo that is
corroborated by captures, real binaries, or real hardware.

## Reading order

0. [service-manual-review.md](service-manual-review.md) — what the XTS 2500 and
   XTS 5000 detailed service manuals contain.
1. [hardware.md](hardware.md) — what the radio is made of.
2. [firmware.md](firmware.md) — what the firmware is and how it is flashed.
3. [protocol-and-codeplug.md](protocol-and-codeplug.md) — what a host can say
   to a running radio, and the codeplug/tuning format.
4. [emulator-plan.md](emulator-plan.md) — how to run the firmware.
5. [open-firmware-plan.md](open-firmware-plan.md) — how to replace it.
6. [EMULATOR_STATUS.md](EMULATOR_STATUS.md) - current emulator state and blocker.
7. [gaps.md](gaps.md) — what is still missing, in priority order.
8. [sources.md](sources.md) — provenance, hashes, and links.

## Related repositories

| Repo | Role |
| --- | --- |
| `RivasMario/open-astro-cps` | Independent RCMP/AT/tuning research, virtual radio server |
| `nyaaaaaaatalie/OpenAutoBench` | Astro 25 tuning commands (deprecated; see OpenAutoBench-ng) |
| `W9CR/Astro-CP-Decoder` | Older Astro/XTS3000 codeplug decoder (not XTS2500) |
| `KFDtool/KFDtool` | Open P25 key fill device |

Vendor service manuals and firmware are in `docs/vendor/` and `firmware/`
(git-ignored). See [sources.md](sources.md) and
[service-manual-review.md](service-manual-review.md).
