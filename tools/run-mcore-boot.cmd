@echo off
setlocal
set "ROOT=%~dp0.."
set "SIM=%~dp0mcore-sim\run.exe"
set "ELF=%~1"
if "%ELF%"=="" set "ELF=%ROOT%\firmware\extracted\host-boot-overlay-emu.elf"
"%SIM%" --memory-region 0x10200000,0x300000 --memory-region 0x12000000,0x100000 --memory-region 0x10000000,0xE000 --memory-region 0x1000E000,0x10000 --memory-region 0x00800000,0x800000 --memory-region 0x13000000,0x100000 --memory-region 0x14000000,0x100000 --endian big --verbose "%ELF%"
exit /b %ERRORLEVEL%
