# Cloud / VPS deploy helper — builds UI, validates env, starts prod compose.
# Usage (repo root):
#   .\scripts\cloud-deploy.ps1 -PublicApiUrl https://api.example.com -PublicUiUrl https://app.example.com
# Prerequisites: Docker engine running, .env.production configured.

param(
    [string]$PublicApiUrl = "",
    [string]$PublicUiUrl = "",
    [string]$EnvFile = ".env.production",
    [switch]$SkipUiBuild,
    [switch]$SkipSmoke,
    [switch]$Down
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Assert-Docker {
    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Docker engine not ready. Start Docker Desktop, then re-run." -ForegroundColor Red
        exit 1
    }
}

Assert-Docker

if ($Down) {
    docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file $EnvFile down
    exit 0
}

if (-not (Test-Path $EnvFile)) {
    Write-Host "Missing $EnvFile — copy from .env.production.example and set secrets." -ForegroundColor Yellow
    Copy-Item .env.production.example $EnvFile
    Write-Host "Created $EnvFile — edit passwords/URLs, then re-run." -ForegroundColor Yellow
    exit 2
}

# Load simple KEY=VAL for UI build
$envMap = @{}
Get-Content $EnvFile | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) { return }
    $i = $line.IndexOf("=")
    if ($i -lt 1) { return }
    $k = $line.Substring(0, $i).Trim()
    $v = $line.Substring($i + 1).Trim()
    $envMap[$k] = $v
}

if ($PublicApiUrl) { $envMap["PUBLIC_API_URL"] = $PublicApiUrl; $envMap["VITE_API_BASE_URL"] = $PublicApiUrl }
if ($PublicUiUrl) {
    $envMap["PUBLIC_UI_URL"] = $PublicUiUrl
    $envMap["CORS_ORIGINS"] = $PublicUiUrl
}

foreach ($req in @("ALA_POSTGRES_URL", "CORS_ORIGINS", "POSTGRES_PASSWORD")) {
    if (-not $envMap.ContainsKey($req) -or $envMap[$req] -match "CHANGE_ME|example.com") {
        Write-Host "Configure $req in $EnvFile (no placeholders)." -ForegroundColor Yellow
    }
}

if (-not $SkipUiBuild) {
    Write-Host "== Building platform-ui ==" -ForegroundColor Cyan
    Push-Location apps/platform-ui
    if (-not (Test-Path node_modules)) { npm ci }
    $env:VITE_API_BASE_URL = if ($envMap["VITE_API_BASE_URL"]) { $envMap["VITE_API_BASE_URL"] } elseif ($envMap["PUBLIC_API_URL"]) { $envMap["PUBLIC_API_URL"] } else { "http://127.0.0.1:8000" }
    $env:VITE_APP_MODE = "private"
    Write-Host "VITE_API_BASE_URL=$env:VITE_API_BASE_URL"
    npm run build
    Pop-Location
    $staticOut = Join-Path $root "releases\ui-static"
    New-Item -ItemType Directory -Force -Path $staticOut | Out-Null
    Copy-Item -Recurse -Force apps\platform-ui\dist\* $staticOut\
    Write-Host "UI static files: $staticOut" -ForegroundColor Green
}

Write-Host "== docker compose (prod overlay) ==" -ForegroundColor Cyan
# Write CORS into env file if provided via params
if ($PublicUiUrl) {
    $content = Get-Content $EnvFile
    $content = $content | ForEach-Object {
        if ($_ -match '^\s*CORS_ORIGINS=') { "CORS_ORIGINS=$PublicUiUrl" }
        elseif ($_ -match '^\s*PUBLIC_UI_URL=') { "PUBLIC_UI_URL=$PublicUiUrl" }
        else { $_ }
    }
    if ($PublicApiUrl) {
        $content = $content | ForEach-Object {
            if ($_ -match '^\s*PUBLIC_API_URL=') { "PUBLIC_API_URL=$PublicApiUrl" }
            elseif ($_ -match '^\s*VITE_API_BASE_URL=') { "VITE_API_BASE_URL=$PublicApiUrl" }
            else { $_ }
        }
    }
    Set-Content $EnvFile $content -Encoding utf8
}

docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file $EnvFile up --build -d

Write-Host "Waiting for API health..." -ForegroundColor Cyan
$ok = $false
for ($i = 0; $i -lt 40; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health/live" -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch { Start-Sleep -Seconds 2 }
}
if (-not $ok) {
    Write-Host "API health not ready. Check: docker compose logs api" -ForegroundColor Red
    exit 1
}

if (-not $SkipSmoke) {
    Write-Host "== production_smoke ==" -ForegroundColor Cyan
    python scripts/production_smoke.py --base http://127.0.0.1:8000
}

Write-Host @"

Deploy stack is up (API on host port from API_PUBLISH_PORT, default 8000).

Next (TLS):
  1. Point DNS for api.* and app.* to this host / LB
  2. Terminate TLS (Caddy/nginx/cloud) → 127.0.0.1:8000 for API
  3. Serve releases/ui-static (or CDN) for the UI with same origin policy / CORS
  4. Confirm CORS_ORIGINS and VITE_API_BASE_URL match real HTTPS URLs
  5. Set ALA_COOKIE_SECURE=1 (already default in prod overlay)

Docs: docs/DEPLOYMENT.md · docs/CLOUD_DEPLOY.md
"@ -ForegroundColor Green
