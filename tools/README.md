# Tools

Small, dependency-free helpers used in this research. They do not contain vendor
code and do not flash anything.

## srec2bin.py

Convert a Motorola S-record to a flat binary and print header/load/entry.

```sh
python3 tools/srec2bin.py input.srec output.bin
python3 tools/srec2bin.py --base 0x100400 input.srec output.bin
```

## cvn_probe.py

Print the header text, entropy, common signatures, and S-record-like content of
a `.cvn` or other firmware container.

```sh
python3 tools/cvn_probe.py firmware/xts2500/XTS2500_DVN4301J_R20.50.09.cvn
```

This is a diagnostic, not a decryptor.

## Building mcore-elf binutils

The host CPU is Motorola M\*CORE. A cross-binutils is enough to disassemble the
Patriot RAM downloader and test images.

```sh
curl -LO https://ftp.gnu.org/gnu/binutils/binutils-2.45.tar.xz
tar xf binutils-2.45.tar.xz
mkdir binutils-build && cd binutils-build
../binutils-2.45/configure --target=mcore-elf --disable-nls --disable-werror \
  --disable-gdb --disable-gdbserver --disable-gprofng --disable-gold \
  --disable-ld --disable-gas --enable-binutils
make -j"$(nproc)"
```

Then:

```sh
# Extract the FlashZap RAR (7z can read RAR).
7z x firmware/tools/astro25_flashzap_for_astro25_radios_admin_admin.rar -o/tmp/flashzap

# Convert the Patriot RAM downloader and disassemble it.
objcopy -I srec -O elf32-mcore-big \
  '/tmp/flashzap/ASTRO25 Flashzap_for_astro25_radios/Flashzap/ramdl/patriot/fzap_flash_ram_dloader.srec' \
  /tmp/patriot.elf
objdump -D /tmp/patriot.elf | less
```

Expected ELF: `ELF 32-bit MSB relocatable, Motorola RCE`.

## Notes

- Vendor firmware, service manuals, and extracted images are git-ignored.
- Do not run FlashZap or write to a radio without a known-good backup.
- Never write partition `0x82`.

## extract_file_package.py

Extract the S-record/`.ish` payloads from a decrypted Depot `filePackage` XML.
This does not decrypt `.cvn`; it parses the XML produced after Depot has
unwrapped it.

```sh
python3 tools/extract_file_package.py \
  firmware/extracted/XTS2500_R20.50.09.decrypted.xml \
  firmware/extracted/package
```

It writes one file per unique `(fileName, fileVersion, destination)` and an
`extracted_manifest.tsv` with sizes and SHA-256 values. Extracted vendor images
remain git-ignored. Use `tools/srec2bin.py` afterward to flatten S-records.
## decrypt_cvn.py

Capture Depot's decrypted `filePackage` XML without a FLASHkey and without
writing to the radio. The tool attaches Frida to a running `PatPortDepot.exe`,
blocks writes to `COM*`, and collects the `CryptDecrypt` output while the user
opens the `.cvn` and starts the firmware update flow.

```powershell
python tools/decrypt_cvn.py `
  --cvn OpenAstro\firmware\xts2500\XTS2500_DVN4228W.cvn `
  --out OpenAstro\firmware\extracted\XTS2500_R17.00.02.decrypted.xml
```

Start Depot first, then run the command and open the package in Depot. Stop when
Depot asks for the FLASHkey. The tool writes the XML only after the closing
`</filePackage>` marker is observed. Extracted vendor images remain git-ignored.
