# Non-canonical archive

These trees are **not** the BC Legal AI product entrypoint. They were moved out of the active monorepo root in the v0.2.0-alpha cleanup so contributors land on the canonical stack only.

## Canonical stack (use these)

| Layer | Path |
|-------|------|
| API | `backend/` — `uvicorn backend.api.main:app` |
| Skills | `skills/` |
| Deterministic services | `services/` |
| Workbench UI | `apps/platform-ui/` |
| Public demo | `huggingface-space-static/` |

See [`docs/CANONICAL_STACK.md`](../../docs/CANONICAL_STACK.md).

## What lives here

| Path | Former location | Why archived |
|------|-----------------|--------------|
| `eap-monorepo/` | repo root | Duplicate “Enterprise AI Platform” monorepo sample |
| `enterprise_ai_platform/` | repo root | Parallel enterprise scaffold / blueprint |
| `apps-api/` | `apps/api/` | EAP FastAPI sample — not the product API |
| `apps-web/` | `apps/web/` | EAP Next.js shell — not the product UI |
| `bc-legal-ai-conversational-platform/` | repo root | Nested packaging experiment / nested copy |
| `zips/` | repo root | Skill/package zip blobs (source already in `skills/`) |

## Policy

- **Do not expand** these trees for product features.
- **Do not** point CI, installers, or README quick-start at these paths.
- History is preserved via `git mv`; restore only if needed for archaeology.
