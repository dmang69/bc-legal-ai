# M1 Platform — build status

**Date:** 2026-07-22  
**Backend:** SQLite by default (`data/ala_platform.sqlite3` or `ALA_SQLITE_PATH`); Postgres via `ALA_POSTGRES_URL`

## Landed

| Capability | Module | API |
|------------|--------|-----|
| Org + user + PBKDF2 passwords | `backend/identity/` | `POST /v1/platform/auth/register`, `login`, `me`, `logout` |
| Sessions (token hash, expiry, revoke) | same | Bearer token |
| Matter create/list/get + membership ACL | `backend/platform/matters.py` | `/v1/platform/matters` |
| Cross-org isolation | tests | — |
| Ethical-wall access level | schema | `matter_members.access_level` |
| Conflict name check | `backend/platform/conflicts.py` | `POST /v1/platform/conflicts/check` |
| Hash-chained audit | `backend/audit/ledger.py` | `GET /v1/platform/audit/verify` |
| Document quarantine + sha256 + text page | `backend/platform/evidence.py` | `.../documents/text` |
| Propositions with provenance fields | same | `.../propositions` |
| Citation fail-closed (s.56 retaliation REJECTED) | `backend/platform/citations.py` | `POST /v1/platform/citations/verify` |
| Knowledge source seed | DB seed | `GET /v1/platform/knowledge/sources` |
| Deadline facade | `backend/platform/deadlines_engine.py` | `POST /v1/platform/deadlines/calculate` |
| SQL migrations | `architecture/contracts/sql/m1_platform.sql` | docker-compose init |
| UI shell against API | `apps/platform-ui` | register/login/matters/citations |

## Not yet (continue M1–M2)

- MFA / OIDC / passwordless  
- Postgres RLS policies  
- Malware scanner engine  
- OCR / PDF page pipeline  
- Full conflict fuzzy + corporate graph  
- Consent ledger persistence on all HITL paths  
- Vector embeddings  
- Redis job workers  
- Court-ready export  

## Run

```bash
uvicorn backend.api.main:app --reload --port 8000
cd apps/platform-ui && npm run dev
```
