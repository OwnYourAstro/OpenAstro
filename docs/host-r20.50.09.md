# Host RAPP R20.50.09 — static analysis

Source: `XTS2500_DVN4301J_R20.50.09.cvn`, unwrapped by Depot and extracted with
`tools/extract_file_package.py`. This document records addresses and behaviour;
the vendor image itself stays in the git-ignored `firmware/extracted/` tree.

## Image

| Property | Value |
| --- | --- |
| File | `XTS2500_R20.50.09_RAPP.srec` / `.bin` |
| Load | `0x10210000` |
| End | `0x104B98BC` |
| Size | `0x2A98BC` (2,791,612 bytes) |
| Architecture | Motorola M*CORE, big-endian |
| Entry | Reset vector at `0x10210000` → `0x10210210` |
| Header | S-record `SWINFORAPPR20.50.09` |

The first `0x200` bytes are a vector table. Entry 0 is `0x10210210`; entries
1–20 point at `0x10210222` … `0x10210274`, followed by `0xFFFFFFFF` padding.
The common exception trampoline is at `0x10210276`.

Reproduce the flat image and disassembly:

```sh
python3 tools/srec2bin.py \
  'firmware/extracted/package/RAPP-R20.50.09-H46.......BN.srec' \
  firmware/extracted/XTS2500_R20.50.09_RAPP.bin
objcopy -I srec -O elf32-mcore-big \
  'firmware/extracted/package/RAPP-R20.50.09-H46.......BN.srec' \
  firmware/extracted/XTS2500_R20.50.09_RAPP.elf
objdump -D firmware/extracted/XTS2500_R20.50.09_RAPP.elf > \
  firmware/extracted/host.dis
```

`objcopy`/`objdump` must be built with `--target=mcore-elf`; a normal host
binutils has no M*CORE disassembler. See `tools/README.md`.

## Reset and exception path

```text
0x10210210  lrw   r2, 0xA0000110
0x10210212  mtcr  r2, psr
0x10210214  lrw   r2, 0x10210000
0x10210216  mtcr  r2, vbr
0x10210218  lrw   r1, 0x110000
0x1021021A  mov   r0, r1
0x1021021C  jsri  0x10218470
0x1021021E  lrw   r7, 0x10210210
0x10210220  jmp   r7
```

The reset code sets `VBR = 0x10210000`, calls `0x10218470` with `r0 =
0x110000`, and then jumps back to the reset address. The loop is the final
fallback; normal execution is expected to stay inside the RTOS.

The exception entries load distinct `0xBADBAD00` … `0xBADBAD14` markers into
`r5`, then branch to `0x10210276`. That trampoline reads `EPC`/`EPSR`, passes
the saved state through `r4`, loads `r0 = 0x110000`, and jumps to
`0x102181A4`. The markers make the exception source visible to the handler.

## Boot chain

| Address | Role |
| --- | --- |
| `0x10218470` | Reset wrapper; saves `r15`, calls `0x10224718`, then `0x102111C8` |
| `0x10224718` | Early board/RTOS initialization; clears globals and starts subsystem init |
| `0x102111C8` | C++/global initialization; installs callback `0x102183BC` at `0x1200BFE8` |
| `0x102102F0` | Kernel/bootstrap path; configures the `0x12000000` control block |
| `0x102181E8` | Timer/clock initialization; called with `2500`, priority `25`, `0x8000`, `0`, `2` |
| `0x102183BC` | Application initialization; installed callback, creates the object table |
| `0x102182CA` | Timer callback registered by `0x102181E8` |

`0x102111C8` clears the watchdog/control register at `0x200000+0x10` and
`+0x14`, initializes the global table at `0x1201EE88`, and calls `0x102102F0`.
`0x102102F0` prepares the RTOS structures rooted at `0x12000000`, calls the
timer setup at `0x102181E8`, then invokes the installed callback at
`0x1200BFE8` (`0x102183BC`) with the argument stored at `0x1200BFEC`.

`0x102183BC` uses the object allocator at `0x10210848` to create 256 entries in
`0x1201F1E8`, pre-populating IDs `30`, `93`, and `118`–`121`. It then returns to
the kernel path. This is the application-level initialization stage.

### RTOS task construction (inferred from `0x102102F0`)

The kernel bootstrap reads the initial task table through pointers in the
`0x12000000` block. The observed loop builds tasks in 32-byte control blocks
and creates a 68-byte initial stack frame for each one.

| Global | Observed use |
| --- | --- |
| `0x12000014` | Task-control-block base pointer |
| `0x12000018` | Initial task configuration table pointer |
| `0x1200001C` | Heap/block-list pointer |
| `0x12000020` | Pointer to the task count |
| `0x12000024` | Initial task stack base |
| `0x12000028` | Initial stack pointer loaded before the C runtime starts |
| `0x12000070` | Saved stack marker destination |
| `0x12000094` / `0x12000098` | Heap block tables |

Each configuration entry appears to be 8 bytes:

```text
+0  byte   task priority
+2  half   stack size
+4  word   task entry point
```

The builder writes the task state, priority, stack pointer, and list links into
the 32-byte control block, then puts the initial `PSR` and entry point into the
68-byte stack frame. After the loop, the kernel invokes the application callback
at `0x1200BFE8`.

### Scheduling primitives (candidate labels)

| Address | Observed behaviour |
| --- | --- |
| `0x10210410` | Updates TCB links/state and conditionally updates `SS3` |
| `0x10210466` | Inserts a TCB into an ordered list keyed by a 32-bit value |
| `0x102104AC` | Restores `PSR`/`EPC` from the saved frame and executes `rte` |
| `0x102104C8` | Reads `0x12000088`, updates counters, and calls the dispatcher |
| `0x102104D0` | Saves current state and walks the timer/list structure |
| `0x10210276` | Exception trampoline; saves `EPC`/`EPSR` and enters `0x102181A4` |

These are not yet named with authority. They are the first addresses to trace
when building a scheduler model.

## Confirmed library routines

| Address | Function | Evidence |
| --- | --- | --- |
| `0x10436084` | `memcpy` | `ldq`/`stq` 16-byte loop, then byte tail |
| `0x10436128` | `memset` | Replicates a byte through a word |
| `0x10436188` | `strcpy` | Copies until NUL |
| `0x104361B0` | `strchr` | Searches for a byte until NUL |
| `0x104361C8` | `strcmp` | Lexicographic byte comparison |
| `0x102185FE` | string-equal helper | Returns 1 for equal strings, 0 otherwise |
| `0x10218632` | `String` constructor | Calls `strlen`, allocates `len + 11`, stores type `0x300` |
| `0x102107D2` | heap/free-list search | Walks the `0x1200001C` block list for a size fit |
| `0x10210640` | heap block handling | Uses the `0x12000094`/`0x12000098` block tables |
| `0x10210848` | object lookup by ID | Walks the object table at `0x12000014` |

## Application surfaces present

The image contains plaintext diagnostics and application strings. Some useful
ones, with virtual addresses:

| Address | String |
| --- | --- |
| `0x1043AFCC` | `RADIO DEBUGGER HELP:` |
| `0x1043C498` | `AT#FZAP=0` |
| `0x1043C4A4` | `AT#FZAP=1` |
| `0x1043C4B0` | `AT#FZAP=2` |
| `0x1043C4BC` | `AT#FZAP=3` |
| `0x1043CD20` | `Starting Deep Reorg of ISH_LP_CODEPLUG` |
| `0x1043D6A4` | `XTS 5000` |
| `0x1043D6B0` | `XTS 2500` |
| `0x1043D890` | `DSP Version:` |
| `0x1043DAA4` | `DVRS Serial Number:` |
| `0x1043DAF8` | `Serial Number:` |
| `0x1043DB14` | `Flash Code:` |
| `0x10458F18` | `R20.50.09` |

The AT command dispatcher is at `0x10222140`. It compares the incoming command
against `AT#FZAP=0` … `AT#FZAP=3` at `0x102221CC`, and feeds other commands to
the debugger/service handlers. The service-report path at `0x1021EF36` prints
`R20.50.09`; the serial/Flashcode report path starts around `0x1021F1F4`.

### FlashZap entry path

`AT#FZAP=0..3` is handled at `0x102221CC`; the actual handler is `0x10219834`.
It reads the argument byte, writes the `"Boot"` marker through the pointer at
`0x10456B9C`, sets the boot baud through `0x10456BA0`, sets
`0x1200086A = 1`, and enters the reset path at `0x10231DC4`.

| Command | Boot baud |
| --- | ---: |
| `AT#FZAP=0` | 57,600 (`0xE100`) |
| `AT#FZAP=1` | 115,200 (`0x1C200`) |
| `AT#FZAP=2` | 230,400 (`0x38400`) |
| `AT#FZAP=3` | 460,800 (`0x70800`) |

This is the host-side path that requests FlashZap/boot mode. It is separate from
the earlier direct SBEP harness, which could not satisfy the bootloader handshake.

The host contains the normal CPS-facing application, not just a bootloader:
codeplug reorg strings, DSP messaging, radio model strings, scan/affiliation
code, and FlashZap entry commands are all present.

## PSDT and boot-ROM interface

The host does not parse PSDT entirely on its own. It calls low-ROM entries at
`0x100104` and `0x1004F4` while initializing the platform data:

- `0x102260C4` calls `0x100104` with no explicit arguments during early
  platform setup.
- `0x102260D8` is the PSDT parser. It reads a base pointer from `0x12000770`,
  adds `0xE000`, checks the `PHDR` magic, walks records starting at
  `PSDT + 0x60`, and copies sections through `0x1004F4`.
- The PSDT sections at `0x1000E000` are `CPLG`, `SECP`, and `TUNE`.
- Other observed low-ROM call targets include `0x100364`, `0x100548`,
  `0x100742`, and `0x100790`.

The task-table/RAM block at `0x12000000` is therefore not initialized by the
RAPP image alone. A faithful emulator needs either a captured boot-RAM image or
stub models for the ROM setup and task configuration.

A machine-readable region/vector map is in [host-map.json](host-map.json).

## Memory-map evidence

| Range | Use |
| --- | --- |
| `0x00000000`–`0x000FFFFF` | low vectors/ROM/peripheral mapping; boot uses `0x110000` |
| `0x00100000`–`0x0010FFFF` | boot/RAM-downloader window seen in FlashZap |
| `0x01600000`–`0x0164B77E` | CFWI MACE boot application (`R07.11.12`) |
| `0x1000E000` | PSDT (`R04.00.00`) |
| `0x10080000`–`0x100D0000` | DSP2/DSPB (`R19.50.01`, 320 KiB each) |
| `0x10210000`–`0x104B98BC` | host RAPP (`R20.50.09`) |
| `0x12000000`–`0x1201FFFF`+ | host RAM globals, RTOS control blocks, object tables |
| `0x200000`+ | watchdog/control registers used during init |

## Current limits

- Function names above are evidence-based labels, not recovered symbols. The
  binary is stripped.
- The `0x12000000` global layout is inferred from instruction operands; it has
  not been reconstructed as a struct.
- The RTOS task table and scheduler state live in RAM and are not present in
  the image.
- No host or DSP code has been executed in an emulator yet.

## Next probes

1. Reconstruct the vector/exception frame and identify the RTOS context-switch
   structure at `0x12000000`.
2. Follow `0x102102F0` into the scheduler and locate the actual task entries and
   priorities.
3. Build a minimal M*CORE memory map for `0x10210000` host code and
   `0x12000000` RAM; stub the `0x200000` watchdog and timer registers.
4. Map the AT command table at the dispatcher (`0x10222140`) and the
   `AT#FZAP` entry path.
