# M*CORE simulator

`run.exe` is a standalone build of the GDB 16.3 `sim/mcore` interpreter with
local emulator fixes for the XTS 2500 host application. It is a research tool,
not a production radio programmer.

## Run

From `OpenAstro`:

```powershell
tools\run-mcore-boot.cmd
```

The runner uses the local synthetic image at:

`firmware\extracted\host-boot-overlay-emu.elf`

That image is generated from extracted firmware and is intentionally not
committed. See `docs/host-r20.50.09.md` and `docs/research-log.md` for the
extraction and overlay notes.

## Current simulator state

- Big-endian M*CORE decoding is forced for the XTS 2500 image.
- `lrw` and `jsri`/`jmpi` literal-pool addressing use the corrected
  instruction-relative base.
- Unaligned accesses are permitted for the synthetic memory map.
- `0x205000`/`0x205004` timer reads and the `0x200000` watchdog window are
  stubbed.
- LCD command/data writes at `0x13000000`/`0x13000001` are captured to
  `mcore-mmio.log` when the logger is enabled in the local build.

The host reaches RTOS and display initialization. The LCD is turned on and
cleared, then firmware blocks in hardware-status/wait loops before the
application UI is drawn. `build\boot-screen.png` is the captured blank LCD
state, not a fabricated boot logo.

## Build notes

The binary was built from GDB 16.3's `sim/mcore` target with MinGW/MSYS2. The
source patches are local research changes; the original GDB source tree is not
committed here. The runtime DLLs next to `run.exe` are MinGW support libraries.

Do not add extracted firmware, `.cvn`, service manuals, or vendor binaries to
this directory.
