# Build the OpenAstro RAM hello payload.
# Set MCORE_BINUTILS to a directory containing gas/as-new.exe,
# ld/ld-new.exe, and binutils/objcopy.exe.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$tools = $env:MCORE_BINUTILS
if (-not $tools) { throw 'Set MCORE_BINUTILS to the mcore-elf binutils build tree.' }
$as = Join-Path $tools 'gas\as-new.exe'
$ld = Join-Path $tools 'ld\ld-new.exe'
$objcopy = Join-Path $tools 'binutils\objcopy.exe'
foreach ($p in @($as, $ld, $objcopy)) { if (-not (Test-Path -LiteralPath $p)) { throw "Missing $p" } }
& $as -EB -o (Join-Path $root 'hello.o') (Join-Path $root 'hello.S')
$script = Join-Path $root 'hello.ld'
& $ld -EB -T $script -o (Join-Path $root 'hello.elf') (Join-Path $root 'hello.o')
& $objcopy -O srec (Join-Path $root 'hello.elf') (Join-Path $root 'hello.srec')
Write-Output 'Built hello.elf and hello.srec'
