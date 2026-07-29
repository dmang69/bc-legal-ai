# Production readiness report — v1.0.0

**Date:** 2026-07-28  
**Repository:** https://github.com/dmang69/bc-legal-ai  
**Release tag:** `v1.0.0`

## Scope of “production ready”

| In scope for v1.0.0 | Out of scope (explicit) |
|---------------------|-------------------------|
| Reproducible install & build | Unsupervised legal advice |
| Auth (register/login/logout, bearer + cookies) | Real-client public SaaS without PIA/pen-test |
| API smoke paths, health probes | LMSYS-class model quality SLAs |
| SQLite + Postgres portable schema | Multi-region active-active |
| CI test + docker + frontend jobs | Org code-signing certs (human-gated) |
| Documented env vars & deploy paths | Guaranteed court-ready AI outputs |

**Product posture remains:** supervised legal *workbench*; `court_ready` stays fail-closed.

## Checklist results

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Frontend builds | **PASS** | `cd apps/platform-ui && npm run build` → Vite production bundle |
| 2 | Backend starts | **PASS** | `uvicorn backend.api.main:app` imports; smoke on :8010 |
| 3 | Env vars documented | **PASS** | `.env.example`, `docs/ENVIRONMENT.md` |
| 4 | Docker image | **CI** | Dockerfile hardened; CI `docker-build` job; local Docker Desktop may be stopped |
| 5 | Database init / migrations | **PASS** | `init_db()` portable DDL; Postgres integration tests in CI |
| 6 | Auth flows | **PASS** | register → me → logout smoke; cookie + CSRF unit tests |
| 7 | API endpoints | **PASS** | pytest **232** (+ 5 Postgres when DSN set); smoke suite |
| 8 | CI pipeline | **PASS** | `.github/workflows/ci.yml` — lint, test, postgres, security, docker, **frontend** |
| 9 | Deploy docs | **PASS** | `docs/DEPLOYMENT.md` |
| 10 | Security review | **PASS (baseline)** | `docs/SECURITY_REVIEW_V1.md` |
| 11 | README install | **PASS** | Updated root README |
| 12 | Release tag | **v1.0.0** | After this gate |

### Automated commands (reproduce)

```bash
# Tests
APP_MODE=development ALA_RATE_LIMIT_DISABLED=1 \
  pytest tests/ -q -m "not postgres_required"
# → 232 passed

# Frontend
cd apps/platform-ui && npm ci && npm run typecheck && npm run build

# Smoke (API must be running)
python scripts/production_smoke.py --base http://127.0.0.1:8000

# Public demo gate
APP_MODE=public_demo python scripts/validate_deployment_readiness.py

# Confidential scan
python scripts/scan_confidential.py .
```

## Residual risks (accepted for v1.0.0)

1. **Docker daemon** not always available on developer Windows hosts — CI remains source of truth for image smoke.  
2. **External LLM / OCR / live web** optional and gated; default is safe_local.  
3. **Compose default passwords** are for local lab only.  
4. **Legal evaluation golden sets** and pen-test remain human/org obligations before real-client data.  
5. **Token still returned in JSON** for API clients (also HttpOnly cookie) — SPA should prefer cookies + CSRF over long-lived localStorage in hardened deployments.

## Sign-off

| Role | Artifact |
|------|----------|
| Engineering gate | This document + green CI on `v1.0.0` |
| Legal / product | Supervising lawyer required before any court filing use |
| Security | Baseline review in `SECURITY_REVIEW_V1.md`; pen-test still recommended |
