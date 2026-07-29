# Cloud deploy runbook (v1.0)

Concrete steps for **Postgres + TLS + CORS + UI** on a VPS or cloud VM.

## 1. Prerequisites

- Docker Engine + Compose plugin  
- Domain names (example):
  - `api.example.com` → API  
  - `app.example.com` → static UI  
- Firewall: 80/443 open; **do not** expose Postgres publicly  

## 2. Configure secrets

```bash
cp .env.production.example .env.production
# Edit:
#   POSTGRES_PASSWORD=...
#   ALA_POSTGRES_URL=postgresql://ala:...@postgres:5432/ala
#   CORS_ORIGINS=https://app.example.com
#   PUBLIC_API_URL=https://api.example.com
#   PUBLIC_UI_URL=https://app.example.com
#   ALA_COOKIE_SECURE=1
#   APP_MODE=production
```

| Variable | Production value |
|----------|------------------|
| `ALA_POSTGRES_URL` | DSN to Postgres service (compose service name `postgres` or managed DB) |
| `CORS_ORIGINS` | Exact UI origin(s), HTTPS, no `*` |
| `ALA_COOKIE_SECURE` | `1` |
| `VITE_API_BASE_URL` | Same as public API URL (build-time for UI) |

## 3. Deploy with helper (Windows)

```powershell
# Start Docker Desktop first if needed
.\scripts\cloud-deploy.ps1 `
  -PublicApiUrl https://api.example.com `
  -PublicUiUrl https://app.example.com
```

This will:

1. Build `apps/platform-ui` with `VITE_API_BASE_URL`  
2. Copy static files to `releases/ui-static/`  
3. `docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up --build -d`  
4. Run `scripts/production_smoke.py` against local API port  

Linux equivalent:

```bash
export VITE_API_BASE_URL=https://api.example.com
export VITE_APP_MODE=private
(cd apps/platform-ui && npm ci && npm run build)
mkdir -p releases/ui-static && cp -r apps/platform-ui/dist/* releases/ui-static/
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up --build -d
python scripts/production_smoke.py --base http://127.0.0.1:8000
```

## 4. TLS (Caddy example)

```caddyfile
api.example.com {
  reverse_proxy 127.0.0.1:8000
}

app.example.com {
  root * /var/www/bc-legal-ui
  file_server
  try_files {path} /index.html
}
```

Copy `releases/ui-static/*` to `/var/www/bc-legal-ui`.

## 5. Managed Postgres (Azure/AWS/GCP)

Instead of compose Postgres:

1. Create managed Postgres 16  
2. Set `ALA_POSTGRES_URL` to the cloud DSN (SSL mode as required, e.g. `?sslmode=require`)  
3. Remove or stop the compose `postgres` service  
4. Ensure the API container can reach the cloud host (VNet / firewall)  

Schema still initializes via app `init_db()` on first boot.

## 6. Verify

```bash
curl -fsS https://api.example.com/health
curl -fsS https://api.example.com/health/ready
python scripts/production_smoke.py --base https://api.example.com
```

Browser: open `https://app.example.com` → register synthetic org → chat.

## 7. Rollback

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production down
# restore previous image tag / UI static bundle
```

## Security reminders

- Change all default passwords  
- Keep `ALA_ALLOW_EXTERNAL_LLM=0` until privacy review  
- Do not enable public demo mode with real data  
- Prefer secret manager over long-lived `.env.production` on disk  
