# Build unsigned Windows installers (NSIS / optional MSI) via Tauri 2.
# Prerequisites: Node 20+, Rust, WebView2, Visual Studio C++ build tools.
# Usage (repo root):
#   powershell -ExecutionPolicy Bypass -File scripts\build_windows_installer.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host '== BC Legal AI Associate - Windows installer build ==' -ForegroundColor Cyan
Write-Host 'Source: apps/platform-ui + apps/desktop-mobile Tauri 2' -ForegroundColor Gray
Write-Host 'Upgrades: same product id ca.bclegalai.associate + higher version replaces prior install' -ForegroundColor Gray

# Verify upgrade config first
Set-Location (Join-Path $root 'apps\desktop-mobile')
if (-not (Test-Path 'node_modules')) { npm install }
node .\scripts\verify-upgrade-config.mjs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Updater artifact signing key (minisign). Required when createUpdaterArtifacts=true.
# Prefer file path; empty password for CI-generated passwordless keys.
$defaultKey = Join-Path $env:USERPROFILE '.tauri\bc-legal-ai-updater.key'
$keyPath = if ($env:TAURI_SIGNING_PRIVATE_KEY_PATH) { $env:TAURI_SIGNING_PRIVATE_KEY_PATH } else { $defaultKey }
if (-not $env:TAURI_SIGNING_PRIVATE_KEY -and (Test-Path $keyPath)) {
  # Normalize to LF single-line-friendly content for Tauri
  $raw = [System.IO.File]::ReadAllText($keyPath).Trim()
  $env:TAURI_SIGNING_PRIVATE_KEY = $raw
  $env:TAURI_SIGNING_PRIVATE_KEY_PATH = $keyPath
  if (-not $env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD) {
    $env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD = ''
  }
  Write-Host "Loaded updater private key from: $keyPath" -ForegroundColor Yellow
} elseif (-not $env:TAURI_SIGNING_PRIVATE_KEY) {
  Write-Host 'WARNING: No updater private key. Generate with:' -ForegroundColor Yellow
  Write-Host '  npx tauri signer generate -w $env:USERPROFILE\.tauri\bc-legal-ai-updater.key' -ForegroundColor Yellow
}

# Frontend
Set-Location (Join-Path $root 'apps\platform-ui')
if (-not (Test-Path 'node_modules')) { npm install }
$env:VITE_APP_MODE = 'workbench'
if (-not $env:VITE_API_BASE_URL) { $env:VITE_API_BASE_URL = 'http://127.0.0.1:8000' }
npm run build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Shell
Set-Location (Join-Path $root 'apps\desktop-mobile')
if (-not (Test-Path 'node_modules')) { npm install }

# Generate full icon set if only png present
if ((Test-Path 'src-tauri\icons\icon.png') -and -not (Test-Path 'src-tauri\icons\icon.ico')) {
  Write-Host 'Generating Tauri icons from icon.png...' -ForegroundColor Yellow
  npx tauri icon src-tauri/icons/icon.png
}

Write-Host 'Running tauri build...' -ForegroundColor Yellow
npx tauri build --config src-tauri/tauri.windows.conf.json
$buildCode = $LASTEXITCODE

$bundle = Join-Path $root 'apps\desktop-mobile\src-tauri\target\release\bundle'
$out = Join-Path $root 'releases\windows'
New-Item -ItemType Directory -Force -Path $out | Out-Null

$installers = @()
if (Test-Path $bundle) {
  $installers = @(Get-ChildItem $bundle -Recurse -Include *-setup.exe,*.msi -ErrorAction SilentlyContinue)
  Get-ChildItem $bundle -Recurse -Include *.exe,*.msi,*.sig,latest.json -ErrorAction SilentlyContinue | ForEach-Object {
    $dest = Join-Path $out $_.Name
    Copy-Item $_.FullName $dest -Force
    Write-Host "Copied $($_.Name) -> $dest" -ForegroundColor Green
  }
  $sumPath = Join-Path $out 'checksums.txt'
  Get-ChildItem $out -File | Where-Object { $_.Name -ne 'checksums.txt' } | ForEach-Object {
    $h = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
    "$h  $($_.Name)"
  } | Set-Content $sumPath -Encoding utf8
  Write-Host "Checksums: $sumPath" -ForegroundColor Green
  Write-Host 'UNSIGNED Authenticode build. Sign before public distribution.' -ForegroundColor Yellow
  Write-Host 'For auto-update: upload installers + .sig + latest.json to GitHub Releases.' -ForegroundColor Cyan
}

if ($buildCode -ne 0 -and $installers.Count -eq 0) {
  Write-Host "Build failed with exit $buildCode and no installers produced." -ForegroundColor Red
  exit $buildCode
}
if ($buildCode -ne 0 -and $installers.Count -gt 0) {
  Write-Host "WARNING: tauri exit $buildCode but installers were produced - often updater .sig step; check TAURI_SIGNING_PRIVATE_KEY." -ForegroundColor Yellow
}

Write-Host 'Done. Publish from releases\windows\ when signed.' -ForegroundColor Cyan
Write-Host 'Sign: scripts\sign_windows_installer.ps1 - see docs\SIGNING_AND_DISTRIBUTION.md' -ForegroundColor Yellow
