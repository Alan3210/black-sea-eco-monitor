@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop_black_sea_monitor.ps1"
echo.
echo Press any key to close this window.
pause >nul
