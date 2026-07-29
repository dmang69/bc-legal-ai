# Production tracks — v0.3.0-alpha foundations

**Date:** 2026-07-28  
**Status:** Internal foundations landed; **not** production certification  

This document describes what shipped for the six production tracks and what remains human/ops-gated.

## 1. Postgres multi-worker

| Item | Status |
|------|--------|
| `ALA_POSTGRES_URL` backend switch | Exists |
| `?` → `%s` placeholder translation | `backend/db/compat.py` + `CompatCursor` |
| Connection pool (`psycopg_pool`) | `backend/db/pool.py` when `ALA_PG_POOL=1` |
| SQLite WAL for single-process | Enabled |
| Multi-worker guidance on `/health` | `multi_worker` object |
| Docker Compose pool env | Set |

**Run multi-worker (Postgres only):**

```bash
export ALA_POSTGRES_URL=postgresql://ala:…@localhost:5432/ala
export ALA_PG_POOL=1
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Do not** run `--workers N` against SQLite.

**Still open:** RLS policies, read replicas, migration zero-downtime, load tests.

## 2. Cookie sessions + CSRF

| Item | Status |
|------|--------|
| HttpOnly `ala_session` cookie on login/register | Yes |
| Non-HttpOnly `ala_csrf` + body `csrf_token` | Yes |
| Bearer still accepted (API/tests) | Yes |
| CSRF required for cookie-only mutating requests | Yes |
| Logout clears cookies | Yes |

**Browser usage:** `fetch(url, { credentials: 'include', headers: { 'X-CSRF-Token': csrf } })`

**Still open:** refresh-token rotation, Secure cookies in all prod edge configs, SPA migration off localStorage where any remains.

## 3. OCR

| Item | Status |
|------|--------|
| Native PDF text (`pypdf`) | `backend/platform/pdf_extract.py` |
| OCR layer + needs_ocr flags | `backend/platform/ocr.py` |
| API `POST …/documents/pdf-extract` | Platform route |
| Optional deps | `pytesseract`, `pdf2image` + system Tesseract/Poppler |

Without OCR packages, empty pages are marked `needs_ocr: true` (fail-closed, no invented text).

## 4. Official-law retrieval

| Item | Status |
|------|--------|
| BC Laws fetcher (allowlisted host) | `knowledgebase/updater/bc_laws_fetcher.py` |
| Currency-line extraction | Best-effort regex |
| Local snapshots under `data/bc_laws_snapshots/` | Optional |
| `court_ready` always false on fetch | Enforced |
| Catalog + fetch API routes | Authenticated platform routes |

**Still open:** full section pin-cites, treatment graph, scheduled currency monitors, human verification workflow UI.

## 5. Court-ready export

| Item | Status |
|------|--------|
| Export manifest gate (approvals + privilege + citations) | Existing |
| ZIP package (DOCX summary + manifest.json) | `backend/platform/court_export.py` |
| Only after `status=APPROVED` | Enforced |
| Public demo blocked | Yes |

**Still open:** form-faithful Form 66/67 PDF, BOA tabs, visual regression, registry e-filing.

## 6. Signed installers

| Item | Status |
|------|--------|
| Unsigned Windows Tauri build script | `scripts/build_windows_installer.ps1` |
| Signing wrapper | `scripts/sign_windows_installer.ps1` |
| Distribution / signing policy | `docs/SIGNING_AND_DISTRIBUTION.md` |

**Human-gated:** code-signing certificate, Apple notarization, store listings. CI must not embed private keys.

## Verification

```bash
pytest tests/ -q
python scripts/scan_confidential.py .
APP_MODE=public_demo python scripts/validate_deployment_readiness.py
```
