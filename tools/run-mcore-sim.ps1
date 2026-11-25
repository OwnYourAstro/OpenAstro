param(
    [string]$Elf = "",
    [switch]$Trace
)

$root = Split-Path -Parent $PSScriptRoot
if (-not $Elf) {
    $Elf = Join-Path $root "firmware\extracted\host-boot-overlay.elf"
}
$sim = Join-Path $PSScriptRoot "mcore-sim\run.exe"
if (-not (Test-Path $sim)) { throw "missing simulator: $sim" }
if (-not (Test-Path $Elf)) { throw "missing ELF: $Elf" }

$args = @(
    "--memory-region", "0x10200000,0x300000",
    "--memory-region", "0x12000000,0x40000",
    "--memory-region", "0x1000E000,0x10000",
    "--endian", "big",
    "--verbose"
)
if ($Trace) { $args += "--trace-insn=on" }
$args += $Elf
& $sim @args
