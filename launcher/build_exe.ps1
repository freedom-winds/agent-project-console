# Build AgentProjectConsole.exe end-to-end on Windows.
#
#   1. install backend + launcher python deps
#   2. install frontend npm deps and run `npm run build`
#   3. generate the icon
#   4. invoke pyinstaller with launcher/tray_app.spec
#
# Output: agent-project-console/dist/AgentProjectConsole.exe
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File launcher/build_exe.ps1
$ErrorActionPreference = "Stop"

$Here = Split-Path -Parent $PSCommandPath        # ...\agent-project-console\launcher
$Root = Resolve-Path "$Here\.."                  # ...\agent-project-console
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

Write-Host "[apc-build] root      : $Root"
Write-Host "[apc-build] backend   : $Backend"
Write-Host "[apc-build] frontend  : $Frontend"

Write-Host ""
Write-Host "[apc-build] (1/4) installing python deps"
python -m pip install -r (Join-Path $Backend "requirements.txt")
python -m pip install -r (Join-Path $Here "requirements.txt")

Write-Host ""
Write-Host "[apc-build] (2/4) building frontend"
Push-Location $Frontend
try {
  if (-not (Test-Path "node_modules")) {
    npm install
  }
  npm run build
} finally {
  Pop-Location
}

if (-not (Test-Path (Join-Path $Frontend "dist\index.html"))) {
  throw "frontend build did not produce dist/index.html"
}

Write-Host ""
Write-Host "[apc-build] (3/4) generating icon"
python (Join-Path $Here "make_icon.py")

Write-Host ""
Write-Host "[apc-build] (4/4) running pyinstaller"
Push-Location $Root
try {
  python -m PyInstaller --noconfirm --clean (Join-Path $Here "tray_app.spec")
} finally {
  Pop-Location
}

$Exe = Join-Path $Root "dist\AgentProjectConsole.exe"
if (Test-Path $Exe) {
  Write-Host ""
  Write-Host "[apc-build] DONE: $Exe"
} else {
  throw "expected $Exe but it was not produced"
}
