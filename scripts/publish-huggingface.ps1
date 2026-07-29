# Publish bc-legal-ai skills package to Hugging Face (Dataset + optional Space)
# Usage:
#   $env:HF_TOKEN = "hf_..."
#   .\scripts\publish-huggingface.ps1 [-Username YOUR_HF_USER] [-Private]

param(
    [string]$Username = "Dmang69",
    [string]$DatasetName = "bc-legal-ai",
    [string]$SpaceName = "bc-legal-ai",
    [switch]$Private,
    [switch]$SkipSpace
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "Running Hugging Face safety validation ..."
& (Get-Command python -ErrorAction Stop).Source "$root\scripts\validate-huggingface-assets.py"
if ($LASTEXITCODE -ne 0) {
    throw "Hugging Face asset validation failed; publication blocked."
}

$hf = (Get-Command hf -ErrorAction SilentlyContinue).Source
if (-not $hf) {
    $candidate = Get-ChildItem "$env:APPDATA\Python\Python*\Scripts\hf.exe" -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending |
        Select-Object -First 1
    if ($candidate) { $hf = $candidate.FullName }
}
if (-not $hf) {
    Write-Host "Install: pip install -U huggingface_hub" -ForegroundColor Yellow
    exit 1
}

if (-not $env:HF_TOKEN -and -not $env:HUGGING_FACE_HUB_TOKEN) {
    Write-Host "Set HF_TOKEN (write token) then re-run." -ForegroundColor Yellow
    Write-Host "Create token: https://huggingface.co/settings/tokens"
    exit 1
}

$token = if ($env:HF_TOKEN) { $env:HF_TOKEN } else { $env:HUGGING_FACE_HUB_TOKEN }
& $hf auth login --token $token --add-to-git-credential 2>&1 | Out-Host

if (-not $Username) {
    $who = & $hf auth whoami 2>&1 | Out-String
    if ($who -match "name['\s:]+([A-Za-z0-9_-]+)") {
        $Username = $Matches[1]
    } else {
        # try JSON
        try {
            $info = & $hf auth whoami 2>&1 | ConvertFrom-Json
            $Username = $info.name
        } catch {
            Write-Host "Pass -Username YOUR_HF_USERNAME" -ForegroundColor Yellow
            exit 1
        }
    }
}

Write-Host "HF user: $Username"

$vis = if ($Private) { "--private" } else { "--public" }

# --- Dataset (skills + lexicon + legislation extracts) ---
$dsId = "$Username/$DatasetName"
Write-Host "Creating dataset $dsId ..."
& $hf repos create $dsId --type dataset $vis --exist-ok 2>&1 | Out-Host

$stage = Join-Path $env:TEMP "bc-legal-ai-hf-dataset"
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory -Path $stage | Out-Null

Copy-Item -Recurse "$root\skills" "$stage\skills"
Copy-Item -Recurse "$root\lexicon" "$stage\lexicon"
Copy-Item -Recurse "$root\checklists" "$stage\checklists"
Copy-Item -Recurse "$root\templates" "$stage\templates" -ErrorAction SilentlyContinue
Copy-Item -Recurse "$root\legislation\court-ready" "$stage\legislation\court-ready"
Copy-Item -Recurse "$root\legislation\scripts" "$stage\legislation\scripts"
Copy-Item "$root\README.md" "$stage\README.md"

# Dataset card
@"
---
license: apache-2.0
language:
  - en
tags:
  - legal
  - british-columbia
  - tenancy
  - skills
  - legislation
pretty_name: BC Legal AI Workbench
---

# BC Legal AI Workbench

Skills and reference materials for BC civil / tenancy / judicial review **legal information** workflows.

**Not legal advice.** Verify legislation on [BC Laws](https://www.bclaws.gov.bc.ca/).

Source repo: GitHub ``bc-legal-ai`` (see README).

## Contents

- ``skills/`` — counsel, tenancy, legislation admin, metacognition, critical reading, etc.
- ``lexicon/`` — living glossary
- ``legislation/court-ready/`` — BC Laws verification logs and extracts
"@ | Set-Content "$stage\README.md" -Encoding utf8

& $hf upload $dsId $stage . --repo-type dataset 2>&1 | Out-Host
Write-Host "Dataset: https://huggingface.co/datasets/$dsId" -ForegroundColor Green

if ($SkipSpace) { exit 0 }

# --- Space (simple Gradio browser of skills + BC Laws links) ---
$spId = "$Username/$SpaceName"
Write-Host "Creating space $spId ..."
& $hf repos create $spId --type space --space-sdk gradio $vis --exist-ok 2>&1 | Out-Host

$spaceDir = Join-Path $root "huggingface-space"
if (-not (Test-Path $spaceDir)) {
    Write-Host "Missing huggingface-space/; run publish after creating Space app files." -ForegroundColor Yellow
    exit 0
}

& $hf upload $spId $spaceDir . --repo-type space 2>&1 | Out-Host
Write-Host "Space: https://huggingface.co/spaces/$spId" -ForegroundColor Green
