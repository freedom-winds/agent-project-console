@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "DATABASE_PATH=%PROJECT_ROOT%backend\instance\apc.sqlite3"
set "DATABASE_URL=sqlite:///%DATABASE_PATH:\=/%"
set "APC_DATABASE_URI=%DATABASE_URL%"
set "SQLALCHEMY_DATABASE_URI=%DATABASE_URL%"
set "APC_DATABASE_PATH=%DATABASE_PATH%"
set "APC_DB_PATH=%DATABASE_PATH%"
set "AGPC_DATABASE_PATH=%DATABASE_PATH%"
set "LOG_PATH=%PROJECT_ROOT%agpc-start.log"

cd /d "%PROJECT_ROOT%"

if not exist "%PROJECT_ROOT%dist\agpc.exe" (
  echo Missing executable: "%PROJECT_ROOT%dist\agpc.exe"
  pause
  exit /b 1
)

if not exist "%DATABASE_PATH%" (
  echo Missing database: "%DATABASE_PATH%"
  pause
  exit /b 1
)

echo Starting AGPC with database:
echo %DATABASE_PATH%
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "$target = [IO.Path]::GetFullPath('%PROJECT_ROOT%dist\agpc.exe'); Get-Process agpc -ErrorAction SilentlyContinue | Where-Object { $_.Path -and ([IO.Path]::GetFullPath($_.Path) -eq $target) } | Stop-Process -Force" >nul 2>nul
powershell -NoProfile -Command "Start-Sleep -Seconds 1" >nul 2>nul

powershell -NoProfile -WindowStyle Hidden -Command "Start-Process -FilePath '%PROJECT_ROOT%dist\agpc.exe' -WorkingDirectory '%PROJECT_ROOT%' -WindowStyle Hidden -RedirectStandardOutput '%LOG_PATH%' -RedirectStandardError '%LOG_PATH%.err'"

endlocal
