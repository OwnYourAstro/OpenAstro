# OpenAstro RAM hello

This is the first custom XTS 2500 host payload. It is **not** a flash image and
must not be written with FlashZap **Write**, **Erase**, or any tuning action.

## What it does

- Runs from SRAM at `0x12040000`.
- Sets the CPU PSR, VBR, and stack expected by the vendor RAM downloader.
- Sends the LCD command sequence recovered from the bootloader descriptor.
- Sends a 5x7 `OpenAstro` bitmap to `0x13000000`.
- Loops forever.

## Current test state

The FlashZap worker can write this image to SRAM at `0x12040000` and read it
back byte-for-byte. The worker's `jump` call returns status `3`; the radio still
shows the bootloader screen, so execution and LCD output remain unproven. Do
not use this payload for a flash write.

The image must not be placed at `0x12000500`: that is inside the active
bootloader and corrupts its jump path.

## Build

Set `MCORE_BINUTILS` to the directory containing the built mcore-elf binutils
tree, then run:

```powershell
.\build.ps1
```

The expected output is `hello.srec`, with entry `0x12040000`.

## Radio test

The earlier Boot Load experiment loaded the vendor bootloader, not this image.
Use the local `build/flashzap_write.exe` SRAM write path instead. It writes only
the selected RAM range and reads it back before attempting a jump.

Keep a verified backup. Do **not** use Write, Erase, Local Bootload, Flash
Marker, or any flash operation. A failed RAM payload is recoverable by
power-cycling.

## Safety

The tuning partition (`0x82`) is per-radio RF calibration and must never be
written. A failed RAM payload is recoverable by power-cycling; a failed flash
write may not be.
## Toolchain

`build.ps1` expects an `mcore-elf` binutils tree with GAS and LD enabled. The
existing local build was configured with:

```sh
../binutils/configure --target=mcore-elf --host=x86_64-w64-mingw32 \
  --enable-gas --enable-ld --enable-binutils --disable-gdb
make -j2 all-gas all-ld MAKEINFO=true
```

Set `MCORE_BINUTILS` to that build directory. Generated `.elf`, `.o`, and
`.srec` files are local build products.
