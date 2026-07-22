# Build Windows .exe for BC Legal AI Associate
# Requires: Python 3.11+, pip
# Usage (from monorepo root):
#   powershell -ExecutionPolicy Bypass -File apps/desktop/build_windows.ps1

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root

Write-Host "Repo: $Root"
Write-Host "Installing build dependencies..."
python -m pip install -q --upgrade pip
python -m pip install -q "fastapi>=0.115" "uvicorn[standard]>=0.30" "pydantic>=2" "pywebview>=5.0" "pyinstaller>=6.0"

Write-Host "Building executable..."
python -m PyInstaller --noconfirm --clean apps/desktop/bc_legal_ai.spec

$exe = Join-Path $Root "dist\BCLegalAIAssociate.exe"
if (Test-Path $exe) {
    Write-Host "OK: $exe"
    Write-Host "Run the .exe to start the local server + UI (loopback only)."
} else {
    Write-Error "Build failed — dist\BCLegalAIAssociate.exe not found"
    exit 1
}
