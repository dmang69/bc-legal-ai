# Publish bc-legal-ai to GitHub
# Usage:
#   $env:GH_TOKEN = "ghp_..."   # classic PAT with repo scope
#   .\scripts\publish-github.ps1 [-Owner dmang69] [-Repo bc-legal-ai] [-Private]

param(
    [string]$Owner = "dmang69",
    [string]$Repo = "bc-legal-ai",
    [switch]$Private
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not $env:GH_TOKEN -and -not $env:GITHUB_TOKEN) {
    Write-Host "Set GH_TOKEN or GITHUB_TOKEN (PAT with repo scope), then re-run." -ForegroundColor Yellow
    Write-Host "Create token: https://github.com/settings/tokens"
    exit 1
}

$token = if ($env:GH_TOKEN) { $env:GH_TOKEN } else { $env:GITHUB_TOKEN }
$headers = @{
    Authorization = "Bearer $token"
    Accept        = "application/vnd.github+json"
    "X-GitHub-Api-Version" = "2022-11-28"
}

$visibility = if ($Private) { $true } else { $false }
$body = @{
    name        = $Repo
    description = "BC Legal AI workbench: counsel skills, tenancy, legislation admin, metacognition"
    private     = $visibility
    auto_init   = $false
} | ConvertTo-Json

Write-Host "Creating repo $Owner/$Repo if missing..."
try {
    Invoke-RestMethod -Method Post -Uri "https://api.github.com/user/repos" -Headers $headers -Body $body -ContentType "application/json" | Out-Null
    Write-Host "Created."
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 422) {
        Write-Host "Repo may already exist; continuing push."
    } else {
        Write-Host "Create failed (will try push anyway): $_" -ForegroundColor Yellow
    }
}

$remote = "https://$token@github.com/$Owner/$Repo.git"
$existing = git remote 2>$null
if ($existing -notcontains "origin") {
    git remote add origin "https://github.com/$Owner/$Repo.git"
} else {
    git remote set-url origin "https://github.com/$Owner/$Repo.git"
}

# Push using token via temporary remote URL
git push "https://x-access-token:$token@github.com/$Owner/$Repo.git" HEAD:master
if ($LASTEXITCODE -ne 0) {
    git push "https://x-access-token:$token@github.com/$Owner/$Repo.git" HEAD:main
}

Write-Host "Done: https://github.com/$Owner/$Repo" -ForegroundColor Green
