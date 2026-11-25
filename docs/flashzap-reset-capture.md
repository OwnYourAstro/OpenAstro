# FlashZap reset capture

This is the local read-only procedure used to capture the XTS 2500 reset window
from a running radio. It does not need a FLASHkey and does not write flash.

## Tool location

The vendor FlashZap client is kept outside git:

`OpenAstro\tools\flashzap\`

Launch:

`OpenAstro\tools\flashzap\fzapclient.exe`

## Procedure

1. Connect the radio and open FlashZap.
2. Select the radio serial port:
   - On the tested setup: `COM20`
   - Baud: `115200`
3. Set **RAM Downloader** to:
   `OpenAstro\tools\flashzap\ramdl\patriot\fzap_flash_ram_dloader.srec`
4. **Actions -> Boot Load**
   - Wait for `Bootload complete`.
5. **Actions -> Unlock**
   - Wait for `Unlock complete`.
6. **Actions -> Read Reset Capture**
   - Save as `r17_reset_capture.srec` (or another local name).

Do not use **Write**, **Erase**, **Local Bootload**, or **Flash Marker**.

## Observed result

The tested R17.00.02 radio produced a 30,720-byte S-record file:

`OpenAstro\build\radio-debugger\r17_reset_capture.srec`

It covers `0x00000000-0x00002FFF` and converts to 12,288 bytes:

```powershell
python OpenAstro\tools\srec2bin.py `
  OpenAstro\build\radio-debugger\r17_reset_capture.srec `
  OpenAstro\build\radio-debugger\r17_reset_capture.bin
```

This is the low reset window; it does not contain the application task table at
`0x12000000`.

## Notes

- `Read Reset Capture` worked after RAM downloader boot load and unlock.
- Generic **Read** of large flash ranges failed with `UNKNOWN_ERROR (257)`.
- A 10 KB probe at `0x00000000` succeeded; it contained low-memory data, not the
  R17 host image.
- Keep the capture and all vendor tools outside git.
