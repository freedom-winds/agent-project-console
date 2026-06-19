@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "SCRIPT=%PROJECT_ROOT%package-and-restart-agpc.ps1"

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"

endlocal
