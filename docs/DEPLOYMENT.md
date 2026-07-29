# Deployment guide

## Architecture (v1 deployable unit)

```text
[ Browser / platform-ui ]  --HTTPS-->  [ Reverse proxy / TLS ]
                                              |
                                    [ uvicorn · FastAPI API ]
                                              |
                     +------------------------+------------------------+
                     |                        |                        |
              Postgres 16               Redis (optional)         MinIO/S3 (optional)
           (multi-user/worker)          rate/cache later          evidence objects later
```

**Canonical process:** `uvicorn backend.api.main:app`  
**UI:** static build of `apps/platform-ui` (or Vite dev proxy for local).

## Local (developer)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev,export,pdf]"
cp .env.example .env
# APP_MODE=development
uvicorn backend.api.main:app --reload --port 8000

# UI
cd apps/platform-ui && npm ci && npm run dev
```

Smoke:

```bash
python scripts/production_smoke.py --base http://127.0.0.1:8000
```

## Docker (API)

```bash
docker build -t bc-legal-ai:1.0.0 .
docker run --rm -p 8000:8000 \
  -e APP_MODE=development \
  -e ALA_RATE_LIMIT_DISABLED=0 \
  bc-legal-ai:1.0.0
curl -f http://127.0.0.1:8000/health
```

## Docker Compose (API + Postgres + Redis + MinIO)

```bash
docker compose up --build
```

Notes:

- Default compose passwords are **dev-only** — change before any shared host.
- App migrations use the **portable M1 schema** at API startup (`init_db()`).
- Optional SQL under `architecture/contracts/sql/v1_data_model.sql` is a **future** full data-model reference; compose no longer auto-runs it into Postgres (avoids schema conflicts).

Multi-worker (Postgres only):

```bash
# in compose override or command:
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Kubernetes

Scaffold manifests live under `infra/k8s/`. Treat as starting point:

1. Inject secrets via SealedSecrets / External Secrets / CSI.  
2. Set `APP_MODE=production`, `ALA_POSTGRES_URL`, `CORS_ORIGINS`, `ALA_COOKIE_SECURE=1`.  
3. Probe `/health/live` and `/health/ready`.  
4. Do not run multiple replicas against SQLite.

## Cloud checklist (Azure / AWS / GCP / VPS)

| Step | Action |
|------|--------|
| 1 | Managed Postgres (or Docker Postgres) with backups |
| 2 | TLS terminator (Caddy, nginx, ALB, Cloudflare) |
| 3 | Run API container or systemd unit |
| 4 | Serve `apps/platform-ui/dist` via CDN/static host; set `VITE_API_BASE_URL` at **build** time |
| 5 | Configure CORS to UI origin only |
| 6 | Secret store for DSN and optional model keys |
| 7 | Run `scripts/production_smoke.py` against staging URL |
| 8 | Enable monitoring on `/health` and 5xx rates |

### UI production build

```bash
cd apps/platform-ui
export VITE_API_BASE_URL=https://api.example.com
export VITE_APP_MODE=private
npm ci
npm run build
# publish dist/
```

## Database migrations

| Backend | Strategy |
|---------|----------|
| SQLite | `init_db()` applies portable `CREATE TABLE IF NOT EXISTS` DDL on startup |
| Postgres | **Same portable DDL** via `CompatCursor` (`?` → `%s`) so app SQL stays unified |
| Reference SQL | `architecture/contracts/sql/*.sql` — design docs / future RLS-pgvector, not required for v1 boot |

Verify:

```bash
# SQLite
python -c "from backend.db import init_db; print(init_db(force=True))"

# Postgres
export ALA_POSTGRES_URL=postgresql://ala:…@host:5432/ala
python -c "from backend.db import init_db, get_db_backend; print(init_db(force=True), get_db_backend())"
pytest tests/test_postgres_integration.py -q
```

## Health endpoints

| Path | Purpose |
|------|---------|
| `GET /health` | Full status (db, multi_worker, public safety) |
| `GET /health/live` | Liveness |
| `GET /health/ready` | Readiness (db + deployment safety) |

## Legal / product constraints (not optional)

This release is **production-ready infrastructure** for:

- synthetic / internal supervised use  
- local private models (Ollama)  
- authenticated multi-user **with Postgres**  

It is **not** a certification for unsupervised real-client legal practice, court filing automation, or public confidential uploads. See `PRODUCT_STATUS.md` and `docs/PRODUCTION_READINESS.md`.
