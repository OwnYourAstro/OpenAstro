# XTS 2500 R17.00.02 host map

Static map derived from the matching decrypted R17 package. Vendor payloads
and extracted binaries remain outside git. See
[EMULATOR_STATUS.md](EMULATOR_STATUS.md) for the current runtime status.

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

The runtime task configuration table is at `0x1201E3D0`, not
`0x12002000`; the boot code rewrites the pointer before the task builder runs.
The table contains 87 eight-byte entries (`priority`, stack size, entry point)
and the TCB base is `0x12001000`. FlashZap `Read Reset Capture` does not expose
this application RAM; reading `0x12000000` returns `UNKNOWN_ERROR (257)`.

Observed task entries include the R17 app callback at task 86, and four tasks
(30-33) sharing entry `0x103B9334`. Task 0 uses low-ROM entry `0x001007DC`.
Selecting only tasks 86 and 30 reaches LCD writes but then traps at PC `0x0`
with `r15=0`, showing a null/low-ROM object call after the table is built. The
UI object constructor is `0x103B4604`; its callers include `0x103BC50C` and
`0x103C5784`. The runtime table is usable, but the missing boot-ROM/DSP objects
are still required.

## Current simulator blocker

The simulator executes the R17 host through RTOS initialization, the
application callback, and into the scheduler/idle loop without faulting. The
callback builds an object lookup table at `0x1201EA58`; entries are R17
RAPP-relative offsets such as `0x00103534` (object 30 -> RAPP `0x10313534`).
Adding the base directly to the table entries caused a fault, so the host code
applies its own relocation when consuming them.

The UI task at `0x103B9334` scans a 30-entry object table at `0x12020730`
(stride `0x10C`). That table is empty in the simulator, which explains why the
task can run without drawing. The remaining blocker is the boot-ROM-populated
object/display state and the low-ROM objects/peripherals it references; the
task table itself is now identified, but the stock UI still does not draw from
the RAPP image alone.
