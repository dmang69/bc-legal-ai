$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Ui = Join-Path $Root "apps/platform-ui"
$TauriSource = Join-Path $Root "apps/desktop-mobile/src-tauri"
$TauriTarget = Join-Path $Ui "src-tauri"

if (-not (Test-Path $TauriTarget)) {
  Copy-Item -Recurse $TauriSource $TauriTarget
}

Set-Location $Ui
npm install
Write-Host "Platform dependencies installed. Run: npm run dev"
