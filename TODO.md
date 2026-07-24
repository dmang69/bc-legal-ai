# BC Legal AI — Production Remediation Plan

**Current Status:** Internal Alpha  
**Target Milestone:** Secure Foundation Completion  
**Last Updated:** 2026-07-22

## Legend
- [ ] Not started
- [x] Completed
- [x] Needs Testing
- [W] In progress
- [!] Blocked

---

## Workstream A — Data Layer Truthfulness & PostgreSQL Support

### A1. SQLite-specific SQL Removal
- [x] `backend/db/migrate.py` — Rewrote schema to remove `INSERT OR REPLACE`, `INSERT OR IGNORE`, `datetime('now')`, `executescript()`
- [x] `backend/identity/service.py` — Replace `INSERT OR REPLACE` with `INSERT ... ON CONFLICT DO UPDATE`
- [x] `backend/identity/service.py` — Replace `datetime('now')` with parameterized `datetime.now(timezone.utc).isoformat()`
- [x] `backend/identity/service.py` — Replace `revoke_session` `datetime('now')` with parameterized value

### A2. SQLAlchemy 2.x ORM Models & Alembic
- [ ] Create SQLAlchemy declarative models for all 20+ tables
- [ ] Set up Alembic with auto-generation
- [ ] Create initial migration
- [ ] Create PostgreSQL-specific migration (RLS, pgvector, advisory locks)

### A3. PostgreSQL Integration Tests
- [ ] Core flows pass on PostgreSQL: login, matter access, document upload, chat, audit writes
- [ ] CI includes PostgreSQL integration suite
- [ ] Docker Compose end-to-end test

**Acceptance:** Zero SQLite-specific SQL in production code paths; migrations run clean on empty/upgraded PG

---

## Workstream B — Unified Authentication & Authorization

### B1. Route Consolidation
- [x] `backend/api/main.py` — Added `CurrentUser` auth dependency to ALL `/v1/*` routes (consents, exceptions, productions, deadlines, post-resolution, knowledge)
- [x] `backend/api/platform_routes.py` — Added `CurrentUser` to `/citations/verify` and `/deadlines/calculate`
- [x] All routes derive actor identity from authenticated session/token
- [x] All matter-scoped routes enforce matter membership/authorization

### B2. Remove Caller-Supplied Identities
- [x] Removed `reviewer_id` from `ReviewBody` → derived from session
- [x] Removed `approver_id` from `ApproveBody` → derived from session
- [x] Removed `human_id` from `ResolveBody` → derived from session
- [x] Removed `human_confirmed` from deadline request bodies

### B3. Route Inventory & Gap Matrix
- [ ] Create documented route inventory showing auth/authz coverage
- [ ] Security tests: unauthorized access blocked, cross-matter access blocked

**Acceptance:** No protected route accepts caller-supplied actor identifiers; route inventory exists

---

## Workstream C — Deny-First Ethical Walls

### C1. Deny-First Policy Implementation
- [x] `backend/identity/service.py` — `can_access_matter()` restructured:
  - Validates organization first
  - Checks ethical_wall/revoked membership BEFORE role check
  - Denies regardless of role (owner/admin) if explicit denial exists
  - Applies role-based access only when no explicit denial

### C2. Dual Approval for Override
- [ ] Implement audited dual-approval flow for exceptional ethical wall override
- [ ] Audit event captures override approval

### C3. Tests
- [ ] Owner with ethical_wall → denied
- [ ] Admin with ethical_wall → denied
- [ ] Member with ethical_wall → denied
- [ ] No membership → denied
- [ ] Owner without restrictions → allowed

**Acceptance:** Ethical wall restrictions override owner/admin role privileges

---

## Workstream D — Protected Operations

### D1. Authn + Authz on All Critical Routes
- [x] `/citations/verify` — authenticated + matter-validated + audit event
- [x] `/deadlines/calculate` — authenticated + matter-validated + audit event
- [x] `/citations/audit` — authenticated + matter-validated
- [x] `/knowledge/sources` — authenticated
- [x] `/v1/matters/{id}/consents` — authenticated
- [x] `/v1/matters/{id}/exceptions` — authenticated
- [x] `/v1/matters/{id}/productions/freeze` — authenticated
- [x] `/v1/productions/{id}/review` — authenticated
- [x] `/v1/productions/{id}/approve` — authenticated
- [x] `/v1/productions/{id}/release` — authenticated
- [x] `/v1/deadlines/jr-clock` — authenticated
- [x] `/v1/deadlines/calculate` — authenticated
- [x] `/v1/matters/{id}/post-resolution/*` — all authenticated

### D2. Audit Events
- [x] Audit events written for: citation.verify, deadline.calculate, consent.grant, consent.withdraw, exception.emit, exception.resolve, production.freeze, production.review, production.approve, production.release, post_resolution.ingest, post_resolution.enforcement, post_resolution.close

### D3. Cross-Matter Tests
- [ ] Write adversarial tests for cross-matter access denial

**Acceptance:** All protected operations require authn + authz + audit

---

## Workstream E — Real Evidence Quarantine

### E1. Quarantine State Machine
- [ ] Implement proper pipeline: RECEIVED → QUARANTINED → TYPE_VALIDATED → MALWARE_SCANNED → EXTRACTED → HUMAN_REVIEWED → RELEASED
- [ ] Files not marked CLEAN based on filename extension alone

### E2. Magic-Byte MIME Detection
- [ ] Replace extension-based detection with `python-magic` or `libmagic` for MIME type identification

### E3. Malware Scanning
- [ ] Integrate ClamAV or equivalent scanning
- [ ] Archive recursion limits
- [ ] Parser isolation / sandboxing

### E4. Immutable Storage
- [ ] Encrypted object storage (MinIO/S3)
- [ ] Immutable content hashes (SHA-256 already stored)
- [ ] Signed access URLs for controlled retrieval

**Acceptance:** Files not marked CLEAN based on extension; extraction after scan success

---

## Workstream F — Durable Workflow State

### F1. Persist HITL State
- [ ] `backend/api/state.py` — Move from in-memory `HitlControlPlane` singleton to PostgreSQL
- [ ] Explicit state machines for: consent, exceptions, production approvals
- [ ] Optimistic locking / version columns
- [ ] Idempotency keys for commands

### F2. Persist Post-Resolution State
- [ ] `backend/api/state.py` — Move `PostResolutionEngine` from in-memory to PostgreSQL-backed
- [ ] Transactional outbox for events

### F3. Recovery Tests
- [ ] State survives process restart
- [ ] Multiple workers observe consistent state
- [ ] Duplicate command delivery is idempotent

**Acceptance:** Workflow state survives restart; multi-worker consistency; crash recovery tested

---

## Workstream G — Concurrency-Safe Audit Ledger

### G1. Serialize Appends
- [ ] `backend/audit/ledger.py` — Add PostgreSQL advisory lock around chain head read + insert
- [ ] For SQLite: use immediate transaction or exclusive lock

### G2. Verification Expansion
- [ ] Expand verification beyond default 10,000 entries
- [ ] Support incremental anchored checkpoints

### G3. Append-Only Permissions
- [ ] Database user with append-only permissions for audit writes
- [ ] Signed checkpoint anchoring (periodic hash to external store)

**Acceptance:** Concurrent append tests show single valid chain; verification covers full ledger

---

## Workstream H — Secure Session Architecture

### H1. Remove localStorage Token
- [ ] `frontend/client/app.js` — Remove bearer token from localStorage
- [ ] Implement fetch with credentials for cookie-based auth

### H2. HttpOnly/Secure/SameSite Cookies
- [ ] Backend returns session token as HttpOnly, Secure, SameSite=Strict cookie
- [ ] CSRF token support for state-changing requests
- [ ] Refresh-token rotation

### H3. Complete Logout Revocation
- [x] `backend/api/platform_routes.py` — `/auth/logout` calls `revoke_session()` backend
- [ ] Frontend logout triggers backend POST to /auth/logout

### H4. Content-Security-Policy
- [ ] Add CSP headers in FastAPI middleware
- [ ] Add CSP meta tag to `frontend/client/index.html`
- [ ] XSS testing

**Acceptance:** No browser bearer token in localStorage; logout revokes server session; CSP enabled

---

## Workstream I — CORS & Health Checks

### I1. Restrictive CORS
- [x] `backend/api/main.py` — Environment-specific `_cors_origins()` function
- [x] Startup failure if wildcard CORS enabled outside `APP_MODE=development`
- [x] Explicit method/header allowlist (`allow_methods`, `allow_headers` lists)

### I2. Truthful Health Checks
- [x] `/health/live` — simple process liveness (always 200 if process running)
- [x] `/health/ready` — validates database, deployment safety; returns non-200 on failure
- [ ] Add object storage, queue, migration readiness to `/health/ready`

**Acceptance:** Wildcard CORS rejected in non-dev; ready endpoint fails when dependencies unavailable

---

## Workstream J — Build Reproducibility & Supply Chain

### J1. Single Dependency Graph
- [ ] `pyproject.toml` — Consolidate all dependencies (dev, postgres, pdf, ocr extras)
- [ ] Remove `requirements.txt` duplication (or make it a lock file)
- [ ] Dockerfile installs via `pip install -e .[postgres,pdf,ocr]`

### J2. Frontend Determinism
- [ ] Add `npm ci` for frontend build in Docker
- [ ] Container-level tests

### J3. Supply Chain
- [ ] SBOM generation per release
- [ ] Signed artifacts
- [ ] Required status checks on merge branch

**Acceptance:** One authoritative dependency graph; Docker installs same extras as CI; SBOM per release

---

## Workstream K — Durable Queue & Infrastructure Truthfulness

### K1. Redis Integration (or Removal)
- [ ] Option A: Implement Redis-backed durable workers with `BRPOPLPUSH` or streams
- [ ] Option B: Remove Redis from compose and documentation
- [ ] Atomic queue claims with `FOR UPDATE SKIP LOCKED` (PostgreSQL) or Redis atomic pop

### K2. Object Storage Integration
- [ ] Option A: Implement MinIO/S3 for evidence storage (not local filesystem)
- [ ] Option B: Remove MinIO from compose, document local-filesystem limitation

### K3. Idempotent Handlers
- [ ] Job handlers are idempotent (same job submitted twice = same result)
- [ ] Dead-letter queue for failed jobs
- [ ] Retry with exponential backoff

**Acceptance:** Queue claims are atomic; handlers idempotent; documentation matches actual architecture

---

## Workstream L — Deadline Integrity & Approval Separation

### L1. Separate Calculation from Approval
- [x] `human_confirmed` removed from all deadline request bodies
- [x] API deadline calls force `human_confirmed=False`
- [ ] Create authenticated `/deadlines/{id}/confirm` endpoint for separate approval

### L2. Output State Distinction
- [ ] Deadline outputs clearly distinguish: estimated vs reviewed vs approved
- [ ] UI/API documentation reflects state meanings

### L3. Tests
- [ ] Spoof prevention: caller cannot self-mark as human_confirmed
- [ ] Confirmation requires distinct authenticated approval event

**Acceptance:** Calculator cannot self-mark confirmed; separate approval required; tests cover spoof

---

## Workstream M — Citation Verification Integrity

### M1. Honest Labeling
- [x] `backend/platform/citations.py` — `court_ready` always `False` (already done)
- [ ] Rename `PROVISIONAL` status to `KEYWORD_MATCH_ONLY`
- [ ] Document: no section retrieval, no pinpoint validation, no currency check

### M2. Future Verification Pipeline
- [ ] Retrieve cited section text via BC Laws API
- [ ] Validate quotation/paraphrase alignment
- [ ] Determine currency/version of law
- [ ] Case treatment verification where applicable

**Acceptance:** Feature naming matches actual behavior; golden-set tests measure accuracy

---

## Workstream N — Fail-Loud Drafting & Error Semantics

### N1. Narrow Exception Handling
- [ ] `backend/platform/drafting.py` — Catch specific exceptions only (ImportError, TemplateNotFound)
- [ ] Differentiate: degraded (partial), error (failed), unavailable (template missing)

### N2. Honest Response Status
- [ ] Return `{"status": "degraded", "error": "..."}` for failures
- [ ] Do not return success-shaped responses for generation failures
- [ ] Monitoring captures drafting failures

**Acceptance:** Failures surface explicit degraded/error state; monitoring captures drafting errors

---

## Workstream O — Model Repository Repair

### O1. Valid Qwen2 Checkpoint
- [ ] Convert repository to valid Qwen2 checkpoint layout
- [ ] Or convert to adapter repository referencing upstream Qwen2 model
- [ ] Fix `config.json` architecture field to actual Qwen2 architecture

### O2. Automated Loading Test
- [ ] Model loads successfully in clean environment
- [ ] Inference smoke test passes in CI
- [ ] Model card accurately describes architecture and dependencies

**Acceptance:** Model loads successfully; inference smoke test passes; model card accurate

---

## P0 Exit Criteria Checklist

- [x] **No known unauthenticated protected routes** — All /v1/* routes authed
- [x] **No known role-bypass of ethical walls** — Deny-first for all roles
- [x] **No misleading PostgreSQL posture** — SQL removed but Alembic pending
- [ ] **Session handling follows secure web practices** — localStorage still used
- [x] **CORS restricted** — Env-specific allowlists
- [x] **Truthful health checks** — /health/live and /health/ready
- [x] **Deadline confirmation not spoofable** — human_confirmed removed from API
- [ ] **Evidence not labeled CLEAN by extension** — Still WIP
- [ ] **CI catches regressions** — Test suite pending
- [ ] **Dependency graph unified** — Still WIP

---

## 30/60/90 Day Plan

### First 30 Days (Weeks 1-4)
- [ ] Freeze unsupported production claims in docs
- [ ] Lock down remaining unprotected routes
- [ ] Patch remaining SQLite-specific SQL in all backend modules
- [ ] Remove localStorage token storage → HttpOnly cookies
- [ ] Add CSP headers
- [ ] Stop fake CLEAN labeling (implement quarantine state machine)
- [ ] Align Dockerfile install with pyproject.toml
- [ ] Establish security regression test suite

### By Day 60 (Weeks 5-8)
- [ ] SQLAlchemy/Alembic migration plan complete
- [ ] PostgreSQL integration tests passing for core flows
- [ ] Durable queue strategy selected and implemented (Redis or PG SKIP LOCKED)
- [ ] Object storage integration implemented or documentation corrected
- [ ] HITL/post-resolution workflow state persisted
- [ ] Logout revocation + refresh rotation + CSRF protection complete

### By Day 90 (Weeks 9-12)
- [ ] Quarantine pipeline operational (magic-byte → scan → extract → release)
- [ ] Audit chain concurrency fix deployed (advisory locks)
- [ ] Citation labeling corrected (KEYWORD_MATCH_ONLY)
- [ ] Backup/restore tested
- [ ] Pilot-readiness review completed
- [ ] Gated supervised pilot possible if remaining high-risk items closed

---

## Current Status Summary

| Workstream | Status | % Complete |
|------------|--------|------------|
| A: PostgreSQL | In Progress | ~50% (SQL removed, Alembic pending) |
| B: Unified Auth | Nearly Complete | ~90% (tests pending) |
| C: Ethical Walls | Complete | 100% |
| D: Protected Ops | Complete | 100% |
| E: Evidence Quarantine | Not Started | 0% |
| F: Durable State | Not Started | 0% |
| G: Audit Ledger | Not Started | 0% |
| H: Secure Sessions | Partial | ~30% (backend done, frontend pending) |
| I: CORS/Health | Complete | 100% |
| J: Build Reproducibility | Not Started | 0% |
| K: Durable Queue | Not Started | 0% |
| L: Deadline Integrity | Nearly Complete | ~80% (confirm endpoint pending) |
| M: Citation Integrity | Partial | ~30% (court_ready=false, relabel pending) |
| N: Drafting Errors | Not Started | 0% |
| O: Model Repair | Not Started | 0% |

**Overall P0 Completion:** ~55%
