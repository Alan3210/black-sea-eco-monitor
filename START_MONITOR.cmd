@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_black_sea_monitor.ps1"
echo.
echo Press any key to close this launcher window.
pause >nul
