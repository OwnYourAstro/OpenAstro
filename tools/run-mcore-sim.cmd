@echo off
setlocal
set "ROOT=%~dp0.."
set "SIM=%~dp0mcore-sim\run.exe"
set "ELF=%ROOT%\firmware\extracted\host-boot-overlay.elf"
if not "%~1"=="" set "ELF=%~1"
"%SIM%" --memory-region 0x10200000,0x300000 --memory-region 0x12000000,0x40000 --memory-region 0x1000E000,0x10000 --endian big --verbose "%ELF%"
exit /b %ERRORLEVEL%
