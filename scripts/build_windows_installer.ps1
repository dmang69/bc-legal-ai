# Build unsigned Windows installers (NSIS / optional MSI) via Tauri 2.
# Prerequisites: Node 20+, Rust, WebView2, Visual Studio C++ build tools.
# Usage (repo root):
#   powershell -ExecutionPolicy Bypass -File scripts\build_windows_installer.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "== BC Legal AI Associate — Windows installer build ==" -ForegroundColor Cyan
Write-Host "Source: apps/platform-ui + apps/desktop-mobile (Tauri 2)" -ForegroundColor Gray

# Frontend
Set-Location "$root\apps\platform-ui"
if (-not (Test-Path "node_modules")) { npm install }
$env:VITE_APP_MODE = "workbench"
$env:VITE_API_BASE_URL = if ($env:VITE_API_BASE_URL) { $env:VITE_API_BASE_URL } else { "http://127.0.0.1:8000" }
npm run build

# Shell
Set-Location "$root\apps\desktop-mobile"
if (-not (Test-Path "node_modules")) { npm install }

# Generate full icon set if only png present
if ((Test-Path "src-tauri\icons\icon.png") -and -not (Test-Path "src-tauri\icons\icon.ico")) {
  Write-Host "Generating Tauri icons from icon.png..." -ForegroundColor Yellow
  npx tauri icon src-tauri/icons/icon.png
}

Write-Host "Running tauri build (unsigned)..." -ForegroundColor Yellow
npx tauri build --config src-tauri/tauri.windows.conf.json

$bundle = Join-Path $root "apps\desktop-mobile\src-tauri\target\release\bundle"
$out = Join-Path $root "releases\windows"
New-Item -ItemType Directory -Force -Path $out | Out-Null

if (Test-Path $bundle) {
  Get-ChildItem $bundle -Recurse -Include *.exe,*.msi | ForEach-Object {
    $dest = Join-Path $out $_.Name
    Copy-Item $_.FullName $dest -Force
    Write-Host "Copied $($_.Name) -> $dest" -ForegroundColor Green
  }
  # checksums
  $sumPath = Join-Path $out "checksums.txt"
  Get-ChildItem $out -File | Where-Object { $_.Name -ne "checksums.txt" } | ForEach-Object {
    $h = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
    "$h  $($_.Name)"
  } | Set-Content $sumPath -Encoding utf8
  Write-Host "Checksums: $sumPath" -ForegroundColor Green
  Write-Host "UNSIGNED build only. Sign before public distribution." -ForegroundColor Yellow
} else {
  Write-Host "Bundle folder not found: $bundle" -ForegroundColor Red
  exit 1
}

Write-Host "Done. Publish artifacts from releases\windows\ to GitHub Releases when signed." -ForegroundColor Cyan
