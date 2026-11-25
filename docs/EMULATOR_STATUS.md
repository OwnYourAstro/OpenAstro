# R17 emulator status

This is the current, evidence-based status of the XTS 2500 emulator work. It is
not a working radio emulator yet.

## Summary

| Area | Status |
| --- | --- |
| Target radio | XTS 2500, model `H46UCF9PW6AN`, serial `123ABC4567` |
| Matching host image | RAPP `R17.00.02`, load `0x10210000`, end `0x10494A68` |
| M\*CORE simulator | Runs the R17 host image through RTOS initialization, the application callback, and the scheduler/idle path |
| Task table | **Identified**: 87 eight-byte runtime configs at `0x1201E3D0` |
| Object lookup table | **Identified**: `0x1201EA58`, RAPP-relative offsets such as object 30 -> `0x10313534` |
| UI object table | **Identified**: `0x12020730`, 30 entries, stride `0x10C`; currently empty |
| Stock UI | **Not booting**. LCD receives only initialization/command traffic |
| Firmware flashing | Not attempted; no FLASHkey or write path was used |

## What works

- The R17 `.cvn` was decrypted with Depot's `CryptDecrypt` path through
  `tools/decrypt_cvn.py`; no FLASHkey was needed.
- The R17 host RAPP is extracted and can be executed by the standalone
  M\*CORE simulator.
- The simulator reaches the R17 reset vector, RTOS bootstrap, application
  callback `0x102183BC`, and the scheduler/idle loop without the earlier
  boot-RAM fault.
- The real runtime task table is now known: 87 entries at `0x1201E3D0`.
  Task 86 is the application callback; tasks 30-33 share entry `0x103B9334`.
- The UI framework is mapped:
  - table `0x12020730`, 30 entries, stride `0x10C`
  - status at `+0`
  - selector at `+21`
  - object pointer at `+96`
  - callable at `+16`
- The UI object constructor is at `0x103B4604`; its callers include
  `0x103BC50C` and `0x103C5784`.
- With a null-call stub and the full task table, the simulator runs without
  the previous fault and emits initialization/command LCD traffic, but no UI
  pixels.

## Live-image integration

The current radio dump was merged into a new simulator image:

- full RAPP `0x10210000..0x10494A67`, matching the R17 package byte-for-byte
- PSDT `0x1000E000..0x1000E71F`, matching the package
- tuning `0x10002000..0x10007FFF`
- DSP `0x10080000..0x100CFFFF`
- reset window `0x00000000..0x00002FFF`
- real `0x00100000..0x0010FFFF` bootflash code from the radio

Artifact: `firmware/extracted/host-boot-r17-romreal.elf`
Runner: `tools/run-mcore-r17-real.cmd`

The integrated image reaches the same scheduler/timer wait loop and issues LCD
initialization/command traffic, but still does not enter the UI draw path. The
real bootflash code did not resolve the missing object/display state.

## Current blocker

The RAPP image schedules the UI tasks but does not contain the low-ROM object
and display implementations they call. When the UI constructor path is forced,
execution reaches `PC 0x0` with `r15=0`, i.e. a missing low-ROM call.

The missing state is the boot-ROM/application-RAM side of the target, especially:

- boot ROM / low-memory object code;
- application RAM around `0x12000000`, including the task state at
  `0x1201E3D0` and the UI table at `0x12020730`;
- the low-ROM object/display implementations that the R17 tasks call.

A full RAM dump is not necessarily required. A boot-ROM image, or a small
capture containing the relevant object/display state, may be enough to keep
this work moving. Without either, the stock UI has to be approximated with
synthetic objects rather than faithfully booted.

## Custom firmware attempt

The first custom RAM payload is in `firmware/hello/` and is linked at
`0x12040000`, outside the active FlashZap RAM downloader. The local
`flashzap_write` worker loaded it over `COM20`, read it back byte-for-byte, and
called the bootloader jump. The jump returned status `3`; the radio stayed on
the vendor bootloader screen, so payload execution and LCD output are still
unproven. No flash write was performed.

## What does not work

- No stock R17 UI is rendered.
- The UI object table is empty.
- The null/low-ROM object call traps or loops at `PC 0x0`.
- The custom RAM payload can be written and verified, but its jump/execution
  path is unresolved.
- No firmware update or flash write has been performed.
- The local FlashZap read harness could not load the vendor DLLs, so a
  boot-ROM read was not captured.

## Next steps

1. Obtain a boot-ROM image, or a small application-RAM capture around
   `0x12000000`/`0x12020730`.
2. If a capture is unavailable, reconstruct the low-ROM object/display
   contract from static evidence and synthetic stubs.
3. Re-run the full task table and verify the UI table is populated.
4. Only after the UI path is understood, move on to custom firmware or
   hello-world hardware work.

## Safety and scope

Read-only inspection is the default. Do not write a codeplug, flash image, or
tuning partition without model/serial/FLASHcode validation and a verified
backup. The tuning partition (`0x82`) holds per-radio RF calibration and must
never be written by experiments. Vendor images and extracted binaries remain
local and are not redistributed.
