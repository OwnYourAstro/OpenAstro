param(
    [string]$Objcopy = "C:\Users\Rose\AppData\Local\Temp\opencode\binutils-build-mingw\binutils\objcopy.exe",
    [string]$Dump = "C:\Users\Rose\Projects\OwnYourAstro\OpenDepot\build\radio-backups\flashdump-r17-20261125",
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)
$ErrorActionPreference = "Stop"
$src = Join-Path $Root "firmware\extracted\host-boot-r17.elf"
$out = Join-Path $Root "firmware\extracted\host-boot-r17-romreal.elf"
if (-not (Test-Path $src)) { throw "missing base ELF: $src" }
if (-not (Test-Path $Dump)) { throw "missing dump directory: $Dump" }
if (-not (Test-Path $Objcopy)) { throw "missing objcopy: $Objcopy" }
$env:PATH = "C:\msys64\mingw64\bin;" + $env:PATH
& $Objcopy --update-section ".sec1=$Dump\rapp-10210000-10494A67.bin" --update-section ".psdt=$Dump\psdt-1000E000.bin" $src $out
& $Objcopy --add-section ".tune=$Dump\tuning-10002000.bin" --set-section-flags .tune=alloc,load,data --change-section-address .tune=0x10002000 $out $out
& $Objcopy --add-section ".reset=$Dump\reset-00000000.bin" --set-section-flags .reset=alloc,load,data --change-section-address .reset=0x0 $out $out
& $Objcopy --add-section ".dsp=$Dump\dsp-10080000-100CFFFF.bin" --set-section-flags .dsp=alloc,load,data --change-section-address .dsp=0x10080000 $out $out
& $Objcopy --update-section ".romstub=$(Join-Path $Root 'build\bootflash-100000.srec.bin')" $out $out
Get-Item $out | Select-Object FullName,Length
