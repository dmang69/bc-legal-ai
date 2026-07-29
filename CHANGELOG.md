# Changelog

## Unreleased

## v0.3.1-alpha — 2026-07-28

### Postgres integration + Form 66

- **Postgres CI:** `test-postgres` job runs `tests/test_postgres_integration.py` against `pgvector/pgvector:pg16`
- **Unified migrations:** portable DDL applied for both SQLite and Postgres (app SQL paths align)
- **Form 66 scaffold:** `backend/platform/form66.py` — Parts 1–4 DOCX (orders, facts, legal basis, materials)
- **API:** `GET /v1/platform/matters/{id}/drafts/form-66.docx` (`X-Form-Number: 66`, never court-ready alone)
- **Court package:** embeds Form 66 under `forms/` when export manifest is APPROVED
- Session expiry compare handles Postgres `timestamptz` objects

## v0.3.0-alpha — 2026-07-28

### Production track foundations

- **Postgres multi-worker:** `CompatCursor` `?`→`%s`, optional `psycopg_pool`, SQLite WAL, `/health.multi_worker`
- **Cookie sessions:** HttpOnly `ala_session` + CSRF double-submit; Bearer still supported; logout clears cookies
- **OCR:** `backend/platform/ocr.py` native+OCR pipeline; API `…/documents/pdf-extract`
- **Official law:** BC Laws fetcher (host allowlist, currency line, snapshots); never auto `court_ready`
- **Court export:** ZIP package (DOCX summary + manifest) only after APPROVED export manifest
- **Signed installers:** `scripts/sign_windows_installer.ps1` + `docs/SIGNING_AND_DISTRIBUTION.md` (certs human-gated)
- Docs: `docs/PRODUCTION_TRACKS_V03.md`

## v0.2.0-alpha — 2026-07-28

### Monorepo archive

- Moved non-canonical trees to `archive/non-canonical/`:
  `eap-monorepo`, `enterprise_ai_platform`, `apps/api`→`apps-api`, `apps/web`→`apps-web`,
  `bc-legal-ai-conversational-platform`, root skill zip blobs
- Root `package.json` is now `bc-legal-ai` with scripts for `backend/` + platform-ui
- Documented archive policy in `archive/non-canonical/README.md` and `docs/CANONICAL_STACK.md`

### P0 security hardening

- Legacy HITL / post-resolution matter routes enforce `require_matter_access` (deny cross-org)
- In-process sliding-window rate limits on `/auth/login` and `/auth/register`
- Security headers middleware: CSP, X-Frame-Options DENY, nosniff, Referrer-Policy
- Tests: ethical wall, cross-matter authz, rate limit 429, security headers

### Repo finalize (prior same-day commit)

- Phase 3/4 HTTP tests for bearer auth; anonymous HITL routes return 401
- Confidential scanner green; deployment-readiness OK (public demo)
- Release notes: `releases/v0.2.0-alpha.md`

### Data model v1.0 (controlling)

- `docs/DATA_MODEL_AND_EVIDENCE_SCHEMA.md` + `architecture/contracts/sql/v1_data_model.sql`
- Postgres 16 + pgvector: users/roles/devices/sessions, matters/participants,
  evidence documents/pages/OCR/embeddings/privilege/custody, evidence items + links,
  authorities + verification, deadlines, drafts, communications, consent, physical files,
  conversations, hash-chained audit_entries
- docker-compose Postgres image: `pgvector/pgvector:pg16`

### M1 platform core (build in progress)

- SQLite default + Postgres SQL (`m1_platform.sql`): orgs, users, sessions, matters,
  membership ACL, parties/conflicts, hash-chained audit, documents/pages/propositions,
  knowledge sources, legal_test_registry seed (s.56 DISABLED)
- API `/v1/platform/*`: register/login, matters, conflicts, evidence quarantine,
  citations, consents, Form 66/67 scaffolds, deadlines, audit verify
- Tests: isolation, audit chain, API flows
- Workbench UI: login/register/matters/citation check against private API

### Platform delivery (Section G)

- Full **Section G** architecture: Workbench / Client / Portal naming; React·TS·Vite·Tauri 2;
  three client modes; OS install/signing/offline/update model; M6A–M6F epics (+55–75 tasks).
- Scaffold: `apps/platform-ui`, `apps/desktop-mobile` (platform confs), `packages/`, PWA CI.
- Docs: `docs/SECTION_G_PLATFORM_AND_DISTRIBUTION.md`.

### Program governance

- Adopted corrected Phase 4 controlling roadmap (`docs/PHASE_4_MASTER_ENGINEERING_PROGRAM.md`):
  ~33–36 workstreams; release levels; modular monolith; Postgres/pgvector/S3/Redis only for V1;
  fine-tune late; Windows approved-folder connector boundary.

## v0.1.0-remediated — 2026-07-21

### M0 Critical Remediation

- Synthetic demo matter fixtures (`DEMO-JR-0001` / `VAN-S-S-999999`)
- Disabled incorrect RTA s.56 retaliation LegalTest + invalidation record
- Confidential scanner + pre-commit + CI workflows
- Section-topic validator; deadline states (HUMAN_CONFIRMED only definitive)
- Public-demo mode guard (`APP_MODE=public_demo`)
- Dockerfile + root docker-compose
- Phase 4 Master Engineering Program document

### Phase 3–4 / 4-4 runtime

- FastAPI HITL + post-resolution API
- Multi-platform install scaffolding (`apps/`, `INSTALL.md`)
