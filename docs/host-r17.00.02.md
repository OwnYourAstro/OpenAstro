# XTS 2500 R17.00.02 host map

Static map derived from the matching decrypted R17 package. Vendor payloads
and extracted binaries remain outside git.

## Image

| Item | Value |
| --- | --- |
| Host RAPP | `R17.00.02` |
| Load | `0x10210000` |
| End | `0x10494A68` |
| Size | `0x284A68` |
| ElF | `firmware/extracted/host-boot-r17.elf` |

## Boot and task path

| Address | Meaning |
| --- | --- |
| `0x10210210` | Reset vector |
| `0x10210276` | Exception trampoline |
| `0x102102F0` | RTOS/bootstrap setup |
| `0x1021035E` | Task config table walk |
| `0x10210698` | Static timer task config: priority 0, stack `0x9C4`, entry `0x102181E8` |
| `0x102181E8` | Timer/clock initialization |
| `0x102183BC` | R17 application callback |
| `0x10218470` | Reset wrapper |

`0x102183BC` creates object IDs `93`, `118`, `119`, `120`, `121`, and `30`
after installing the timer task. These are application objects, not the
runtime task table.

## Memory

| Item | Value |
| --- | --- |
| Host RAM | `0x12000000`-`0x120FFFFF` |
| PSDT | `0x1000E000`, R04.00.00 |
| Flash | 8 MB |
| Reset capture | `0x00000000`-`0x00002FFF` |

The runtime task configuration table at `0x12002000` and the TCB base at
`0x12001000` are boot-ROM populated. FlashZap `Read Reset Capture` does not
expose this application RAM; reading `0x12000000` returns `UNKNOWN_ERROR (257)`.

## Current simulator blocker

The simulator executes the R17 host through RTOS initialization and reaches
the application object setup. It still faults on boot-RAM-derived pointers
before the UI task is drawn. The missing input is the real R17 boot-RAM/task
table, not another copy of the RAPP image.
