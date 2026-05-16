# Start backend (Flask on 127.0.0.1:8765) and frontend (Vite on 127.0.0.1:5173)
# Usage: powershell -ExecutionPolicy Bypass -File scripts\dev.ps1

$ErrorActionPreference = "Stop"
$root = Resolve-Path "$PSScriptRoot\.."
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

if (-not (Test-Path "$backend\requirements.txt")) {
  Write-Error "backend not found at $backend"
}
if (-not (Test-Path "$frontend\package.json")) {
  Write-Error "frontend not found at $frontend"
}

Write-Host "[apc] starting backend (http://127.0.0.1:8765)"
$backendProc = Start-Process -FilePath "python" -ArgumentList "run.py" -WorkingDirectory $backend -PassThru -NoNewWindow

Start-Sleep -Seconds 2

Write-Host "[apc] starting frontend (http://127.0.0.1:5173)"
$frontendProc = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory $frontend -PassThru -NoNewWindow

Write-Host ""
Write-Host "Backend  PID = $($backendProc.Id)"
Write-Host "Frontend PID = $($frontendProc.Id)"
Write-Host "Press Ctrl-C to stop. To stop manually:  Stop-Process -Id $($backendProc.Id),$($frontendProc.Id)"

try {
  Wait-Process -Id $backendProc.Id, $frontendProc.Id
} finally {
  if (-not $backendProc.HasExited) { Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue }
  if (-not $frontendProc.HasExited) { Stop-Process -Id $frontendProc.Id -Force -ErrorAction SilentlyContinue }
}
