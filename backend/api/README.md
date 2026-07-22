# Phase 3–4 / 4-4 API

```bash
# from monorepo root
pip install fastapi uvicorn httpx pydantic
uvicorn backend.api.main:app --reload --port 8000
# docs: http://127.0.0.1:8000/docs
```

## Routes

| Area | Paths |
|------|--------|
| HITL consent | `/v1/matters/{id}/consents`, `/v1/consents/evaluate-operation`, withdraw |
| Exceptions | `/v1/matters/{id}/exceptions`, resolve |
| Productions | freeze / review / approve / release |
| JR clock | `/v1/deadlines/jr-clock` |
| Post-resolution 4-4 | ingest, status, enforcement, close |
| Knowledge | sources, citation verify |

In-memory only until Postgres (`architecture/contracts/sql/phase3_core.sql`) is wired.
