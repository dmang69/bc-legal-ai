# Sign Windows installer artifacts with Authenticode (human-supplied cert).
# Prerequisites: Windows SDK signtool.exe, PFX or cert store access.
# Usage (repo root):
#   $env:ALA_SIGN_PFX = "C:\secure\codesign.pfx"
#   $env:ALA_SIGN_PFX_PASSWORD = "..."
#   powershell -ExecutionPolicy Bypass -File scripts\sign_windows_installer.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$out = Join-Path $root "releases\windows"

if (-not (Test-Path $out)) {
  Write-Host "No releases/windows folder. Build first: scripts\build_windows_installer.ps1" -ForegroundColor Red
  exit 1
}

$signtool = $null
$candidates = @(
  "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\signtool.exe",
  "${env:ProgramFiles}\Windows Kits\10\bin\*\x64\signtool.exe"
)
foreach ($pattern in $candidates) {
  $found = Get-Item $pattern -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
  if ($found) { $signtool = $found.FullName; break }
}
if (-not $signtool) {
  Write-Host "signtool.exe not found. Install Windows SDK." -ForegroundColor Red
  exit 1
}

$timestamp = if ($env:ALA_SIGN_TIMESTAMP_URL) { $env:ALA_SIGN_TIMESTAMP_URL } else { "http://timestamp.digicert.com" }
$files = Get-ChildItem $out -File | Where-Object { $_.Extension -in ".exe", ".msi" }
if (-not $files) {
  Write-Host "No .exe/.msi in $out" -ForegroundColor Red
  exit 1
}

if (-not $env:ALA_SIGN_PFX) {
  Write-Host "Set ALA_SIGN_PFX to your .pfx path (from a secret store). Aborting." -ForegroundColor Yellow
  Write-Host "Artifacts remain UNSIGNED in $out" -ForegroundColor Yellow
  exit 2
}

foreach ($f in $files) {
  Write-Host "Signing $($f.Name)..." -ForegroundColor Cyan
  $args = @(
    "sign", "/fd", "SHA256", "/td", "SHA256", "/tr", $timestamp,
    "/f", $env:ALA_SIGN_PFX
  )
  if ($env:ALA_SIGN_PFX_PASSWORD) {
    $args += @("/p", $env:ALA_SIGN_PFX_PASSWORD)
  }
  $args += $f.FullName
  & $signtool @args
  if ($LASTEXITCODE -ne 0) { throw "signtool failed for $($f.Name)" }
}

$sumPath = Join-Path $out "checksums.txt"
Get-ChildItem $out -File | Where-Object { $_.Name -ne "checksums.txt" } | ForEach-Object {
  $h = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
  "$h  $($_.Name)"
} | Set-Content $sumPath -Encoding utf8

$notes = Join-Path $out "release-notes.md"
@"
# Windows artifacts (signed)

Signed with Authenticode (SHA256). Verify:

``````
Get-AuthenticodeSignature .\releases\windows\*.exe
``````

Not legal advice. Do not use for confidential client data on public demos.
"@ | Set-Content $notes -Encoding utf8

Write-Host "Done. Updated checksums: $sumPath" -ForegroundColor Green
