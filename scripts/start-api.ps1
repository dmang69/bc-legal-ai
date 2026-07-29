# Start BC Legal AI API from any directory.
# Usage:  pwsh -File C:\Users\Dizzle\.grok\worktrees\ai-legal-bc-legal-ai\legal-ai\scripts\start-api.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "Repo root: $Root" -ForegroundColor Cyan
Write-Host "Starting API on http://127.0.0.1:8000 ..." -ForegroundColor Green

$env:APP_MODE = if ($env:APP_MODE) { $env:APP_MODE } else { "development" }
$env:PYTHONPATH = $Root

python -m uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000
