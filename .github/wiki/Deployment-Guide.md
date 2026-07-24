# Deployment Guide

## Deployment Options

### Option 1: Docker Compose (Development/Staging)

```bash
# Build and start all services
docker compose up --build -d

# Verify
curl http://localhost:8000/health
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

### Option 2: Kubernetes (Production)

```bash
# Using Helm
helm upgrade --install ala ./infra/k8s/helm \
    --namespace ala \
    --create-namespace \
    --values ./infra/k8s/helm/values-production.yaml

# Verify deployment
kubectl get pods -n ala
kubectl get svc -n ala
```

### Option 3: Bare Metal / VM

```bash
# Prerequisites: Python 3.12+, PostgreSQL 16+, Redis 7+
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev,postgres,pdf,ocr]"

# Configure environment
export APP_MODE=production
export ALA_POSTGRES_URL=postgresql://user:pass@localhost:5432/ala
export ALA_REDIS_URL=redis://localhost:6379/0
export CORS_ORIGINS=https://app.example.com

# Run
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Environment Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_MODE` | `development` | `development`, `production`, `public_demo` |
| `ALA_POSTGRES_URL` | — | PostgreSQL connection string |
| `ALA_SQLITE_PATH` | `data/ala_platform.sqlite3` | SQLite path (dev only) |
| `ALA_REDIS_URL` | — | Redis connection string |
| `ALA_S3_ENDPOINT` | — | MinIO/S3 endpoint |
| `CORS_ORIGINS` | `*` (dev) | Comma-separated allowed origins |
| `SECRET_KEY` | — | Session encryption key (auto-generated if absent) |

## Health Checks

| Endpoint | Purpose |
|----------|---------|
| `/health/live` | Process liveness (always 200) |
| `/health/ready` | Readiness (DB, queue, storage) |
| `/health` | Legacy status endpoint |

## Production Checklist

- [ ] PostgreSQL with RLS enabled
- [ ] Redis configured for queue/rate limiting
- [ ] MinIO/S3 for encrypted evidence storage
- [ ] CORS origins restricted
- [ ] MFA enforced for all users
- [ ] Audit chain verification scheduled
- [ ] Backup/restore tested
- [ ] SBOM generated for release
- [ ] Penetration test passed
- [ ] Legal review completed
