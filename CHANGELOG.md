# Changelog

## Unreleased

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
