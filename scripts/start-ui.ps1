# Start platform-ui (Vite) from any directory.
# Usage:  pwsh -File C:\Users\Dizzle\.grok\worktrees\ai-legal-bc-legal-ai\legal-ai\scripts\start-ui.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Ui = Join-Path $Root "apps\platform-ui"
Set-Location $Ui

Write-Host "UI dir: $Ui" -ForegroundColor Cyan
Write-Host "Starting Vite on http://127.0.0.1:1420 ..." -ForegroundColor Green

if (-not (Test-Path "node_modules")) {
  npm install
}
npm run dev
