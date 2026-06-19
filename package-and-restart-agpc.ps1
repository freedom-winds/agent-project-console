$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSCommandPath
$Dist = Join-Path $ProjectRoot "dist"
$BuiltExe = Join-Path $Dist "AgentProjectConsole.exe"
$AgpcExe = Join-Path $Dist "agpc.exe"
$DatabasePath = Join-Path $ProjectRoot "backend\instance\apc.sqlite3"
$LogPath = Join-Path $ProjectRoot "agpc-start.log"

function Get-ProjectAgpcProcess {
  $targets = @()
  if (Test-Path $AgpcExe) {
    $targets += [IO.Path]::GetFullPath($AgpcExe)
  }
  if (Test-Path $BuiltExe) {
    $targets += [IO.Path]::GetFullPath($BuiltExe)
  }

  Get-Process agpc, AgentProjectConsole -ErrorAction SilentlyContinue |
    Where-Object {
      $_.Path -and ($targets -contains [IO.Path]::GetFullPath($_.Path))
    }
}

Push-Location $ProjectRoot
try {
  Write-Host "[agpc] building frontend"
  Push-Location (Join-Path $ProjectRoot "frontend")
  try {
    npm.cmd run build
  } finally {
    Pop-Location
  }

  Write-Host "[agpc] building executable"
  py -3.12 -m PyInstaller --noconfirm --clean (Join-Path $ProjectRoot "launcher\tray_app.spec")

  if (-not (Test-Path $BuiltExe)) {
    throw "expected build output not found: $BuiltExe"
  }

  Write-Host "[agpc] stopping current project instance"
  Get-ProjectAgpcProcess | Stop-Process -Force
  Start-Sleep -Seconds 1

  Copy-Item -LiteralPath $BuiltExe -Destination $AgpcExe -Force

  $env:APC_DATABASE_URI = "sqlite:///" + ($DatabasePath -replace "\\", "/")
  $env:SQLALCHEMY_DATABASE_URI = $env:APC_DATABASE_URI

  Write-Host "[agpc] starting updated instance"
  Start-Process -FilePath $AgpcExe `
    -WorkingDirectory $ProjectRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput $LogPath `
    -RedirectStandardError "$LogPath.err"
} finally {
  Pop-Location
}
