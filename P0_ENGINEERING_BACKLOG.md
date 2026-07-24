# P0 Engineering Backlog — Secure Foundation

**Source:** `BC_Legal_AI_Production_Remediation_Plan_2026-07-22.md`  
**Baseline reviewed:** 2026-07-23 repository state  
**Release target:** Gate 0 — no real client data, multi-tenant deployment, or public beta before every P0 exit criterion passes.

## Operating rules

- Every ticket is independently assignable and must land with tests, migration/rollback notes, observability, and operator evidence.
- PostgreSQL is the production authority. SQLite remains a local-test/development backend only during migration.
- Matter isolation and ethical walls are deny-first. Authentication alone is never matter authorization.
- Court-ready output remains fail-closed until citation, evidence, privilege, and human-approval gates pass.
- Estimates are engineering days and exclude security/legal review wait time.

## Priority and dependencies

| ID | Ticket | Owner profile | Estimate | Depends on | Gate evidence |
|---|---|---:|---:|---|---|
| P0-01 | Establish versioned PostgreSQL migration runner | Backend/DB | 2d | — | Upgrade/rollback logs in CI |
| P0-02 | Remove service-layer SQLite SQL assumptions | Backend | 3d | P0-01 | Dual-backend CRUD suite |
| P0-03 | Enforce tenant RLS and database roles | Security/DB | 3d | P0-01 | Cross-org denial tests |
| P0-04 | Close route-level authorization gaps | Backend/Security | 3d | P0-03 | Route matrix tests |
| P0-05 | Implement secure browser sessions and CSRF | Full stack/Security | 5d | P0-01 | Cookie/CSRF/logout tests |
| P0-06 | Serialize audit-ledger appends | Backend/DB | 3d | P0-01 | 100-writer chain test |
| P0-07 | Make audit storage append-only and anchored | Security/Platform | 3d | P0-06 | Role-denial and signature verification |
| P0-08 | Implement evidence quarantine state machine | Backend/Security | 5d | P0-01 | Malicious fixture suite |
| P0-09 | Integrate immutable MinIO evidence storage | Platform | 4d | P0-08 | Versioning and signed-access tests |
| P0-10 | Persist HITL workflow state | Backend/DB | 6d | P0-01, P0-03 | Restart and multi-worker tests |
| P0-11 | Persist post-resolution workflow state | Backend/DB | 4d | P0-01, P0-03 | Restart and concurrency tests |
| P0-12 | Implement atomic durable job processing | Backend/Platform | 4d | P0-01 | Competing-worker/lease tests |
| P0-13 | Integrate Redis queue and dead-letter flow | Platform | 3d | P0-12 | Crash/reclaim/DLQ evidence |
| P0-14 | Implement authoritative citation verification | Legal-tech/Backend | 8d | P0-01 | BC Laws fixture and currency suite |
| P0-15 | Repair Hugging Face model packaging | ML platform | 1d | — | Clean model-load smoke test |
| P0-16 | Add security telemetry, backup, and recovery | SRE/Security | 4d | P0-03, P0-09 | Alert and restore drill |
| P0-17 | Execute Gate 0 adversarial release suite | QA/Security | 5d | P0-01–16 | Signed gate report |

## Executable tickets

### P0-01 — Establish versioned PostgreSQL migration runner

**Problem:** `backend/db/migrate.py` splits SQL on semicolons and has no durable PostgreSQL migration ledger, transactional version ordering, or rollback discipline.

**Scope**
- Replace ad-hoc SQL splitting with Alembic or an equivalent versioned runner.
- Reconcile `phase3_core.sql`, `m1_platform.sql`, and `v1_data_model.sql` into one ordered schema authority.
- Record version, checksum, applied time, and deployment identity.
- Add expand/contract and rollback conventions; migrations must be idempotent only where explicitly designed.

**Acceptance**
- [ ] Empty PostgreSQL 16 database upgrades to head in one command.
- [ ] Upgrade is repeat-safe and checksum drift fails deployment.
- [ ] Previous release can run during expand phase; rollback rehearsal is documented and tested.
- [ ] CI tests upgrade from empty and from the last supported schema snapshot.

**Verification:** migration CI logs, schema dump diff, rollback rehearsal.  
**Rollback:** restore pre-migration snapshot or execute tested downgrade before contract phase.

### P0-02 — Remove service-layer SQLite SQL assumptions

**Scope**
- Use one parameter adapter/repository API in `backend/db/helpers.py`, or SQLAlchemy Core.
- Cover `backend/platform/jobs.py`, `consent_store.py`, `conflicts.py`, `citations.py`, `workspace.py`, `conversation.py`, `backend/audit/ledger.py`, and identity/matter stores.
- Parameterize UTC timestamps; remove `?` leakage, SQLite date functions, `INSERT OR ...`, `executescript`, and implicit row-id assumptions.

**Acceptance**
- [ ] Identical CRUD contract tests pass on SQLite and PostgreSQL.
- [ ] Static check finds no prohibited SQLite-only patterns outside dialect adapters/migrations.
- [ ] PostgreSQL paths use native transactions and return mappings consistently.

### P0-03 — Enforce tenant RLS and database roles

**Scope**
- Add `org_id` to every tenant-owned table and validate backfill.
- Enable and force PostgreSQL RLS for matters, memberships, documents/pages/propositions, consents, conversations/messages, exports, HITL, post-resolution, citations, and jobs where tenant-owned.
- Set transaction-local `app.org_id` and `app.user_id`; create runtime, migration, audit-writer, and read-only roles.
- Ethical-wall denial remains an application invariant and gains database-backed tests.

**Acceptance**
- [ ] Runtime role cannot bypass RLS or set another organization context.
- [ ] Cross-org and cross-matter reads/writes fail for every tenant table.
- [ ] Owner/admin cannot bypass an ethical wall.
- [ ] Connection-pool reuse cannot leak tenant context.

### P0-04 — Close route-level authorization gaps

**Scope**
- Apply `require_matter_access` with read/write/admin levels to every matter-bound route and resolve resource IDs to matters before acting.
- Fix direct gaps in `backend/api/main.py` HITL, production, and post-resolution routes.
- Fix `evaluate-ai` and any service-only implicit checks; explicitly classify public metadata routes.
- Add centralized policy dependencies and deny-by-default route tests.

**Acceptance**
- [ ] Every protected route returns 401 without credentials, 403/404 for inaccessible resources, and success only at the required level.
- [ ] Resource-ID routes cannot be used as IDOR paths.
- [ ] Route matrix has no unexplained `GAP` rows.

### P0-05 — Implement secure browser sessions and CSRF

**Scope**
- Replace frontend bearer-token storage with opaque server sessions in `Secure`, `HttpOnly`, `SameSite=Strict` cookies.
- Add CSRF protection for every state-changing cookie-authenticated request.
- Rotate session/refresh credentials; revoke server-side on logout, password change, suspension, and security events.
- Add CSP and security headers; rate-limit login/register and protect against account enumeration.

**Acceptance**
- [ ] No auth secret appears in local/session storage or JavaScript-readable cookies.
- [ ] Missing/invalid CSRF fails mutations; logout revokes and clears credentials.
- [ ] Fixation, rotation, expiry, replay, and parallel-session tests pass.
- [ ] CSP/security-header integration tests pass.

### P0-06 — Serialize audit-ledger appends

**Scope**
- Maintain a per-chain head row locked with `SELECT ... FOR UPDATE` or an advisory transaction lock.
- Compute predecessor and hash inside one transaction; use `BEGIN IMMEDIATE` only in the SQLite adapter.
- Support complete and bounded-range verification without a hidden 10,000-row limit.

**Acceptance**
- [ ] 100 concurrent writers produce one valid, totally ordered chain.
- [ ] No duplicate predecessor race occurs.
- [ ] Failure before commit leaves neither event nor head partially updated.

### P0-07 — Make audit storage append-only and anchored

**Scope**
- Deny runtime `UPDATE`, `DELETE`, and `TRUNCATE`; use a dedicated audit writer.
- Generate periodic signed checkpoints and store copies outside the primary database.
- Define key rotation, verification, retention, and alerting procedures.

**Acceptance**
- [ ] Runtime tampering commands fail in integration tests.
- [ ] Independent verifier validates signed checkpoints and detects altered/missing rows.
- [ ] Invalid chain/checkpoint raises a production alert.

### P0-08 — Implement evidence quarantine state machine

**Scope**
- Enforce `RECEIVED → QUARANTINED → TYPE_VALIDATED → MALWARE_SCANNED → EXTRACTED → HUMAN_REVIEWED → RELEASED`; terminal `BLOCKED` is allowed from controlled stages.
- Quarantine before parsing; detect MIME by content, reject dangerous/polyglot/nested executable content, and integrate real AV.
- Store transition history and page/span status; audit every transition.

**Acceptance**
- [ ] Processing APIs cannot access non-`RELEASED` objects.
- [ ] EICAR, misleading extensions, malformed PDFs, archive bombs, and polyglot fixtures fail closed.
- [ ] Scanner unavailable/timeout never marks an object clean.
- [ ] Every transition is authorized, validated, and audited.

### P0-09 — Integrate immutable MinIO evidence storage

**Scope**
- Introduce a storage interface with MinIO/S3 production implementation and filesystem test adapter.
- Separate quarantine and released buckets/prefixes; enable versioning, encryption, retention, and no-overwrite object keys.
- Issue short-lived scoped signed URLs only after authorization and release-state checks.

**Acceptance**
- [ ] Production mode refuses filesystem evidence storage.
- [ ] Original bytes/hash/version survive processing and overwrite attempts.
- [ ] Signed URL cannot cross tenant/matter boundaries and expires as configured.

### P0-10 — Persist HITL workflow state

**Scope**
- Persist consent, exception, escalation, production, review, approval, and release states.
- Add optimistic versions, idempotency keys, actor/org/matter ownership, and transactional outbox events.
- Enforce valid state transitions and reviewer/approver separation transactionally.

**Acceptance**
- [ ] State survives restart and is identical across 3+ workers.
- [ ] Duplicate requests do not duplicate grants/events/actions.
- [ ] Invalid or stale transitions fail without partial audit/state writes.

### P0-11 — Persist post-resolution workflow state

**Scope**
- Persist outcomes, compliance events, escalation tickets, JR clocks/petitions, stays, enforcement packages, and retention closures.
- Add idempotency/versioning and locked due-clock processing.

**Acceptance**
- [ ] Complete state survives restart and multi-worker access.
- [ ] Concurrent clock processing produces one action.
- [ ] Every state mutation requires matter authorization and creates an audit event.

### P0-12 — Implement atomic durable job processing

**Scope**
- Define backend-neutral enqueue/claim/ack/fail/reclaim contract.
- PostgreSQL uses atomic claim with `FOR UPDATE SKIP LOCKED`; add lease, heartbeat, retries, maximum attempts, idempotency, and payload hashes.

**Acceptance**
- [ ] Competing workers never claim the same active lease.
- [ ] Crashed work is reclaimed after expiry.
- [ ] Handler effects are idempotent; retry exhaustion enters DLQ.

### P0-13 — Integrate Redis queue and dead-letter flow

**Scope**
- Use Redis Streams consumer groups or a proven queue library—not bare `BLPOP`—with acknowledgment, pending recovery, and DLQ.
- Make Redis production-required when configured and report queue readiness truthfully.

**Acceptance**
- [ ] Queue survives worker restart and recovers pending work.
- [ ] Redis outage fails safely without silent SQLite fallback in production.
- [ ] Operators can inspect/replay DLQ entries with authorization and audit.

### P0-14 — Implement authoritative citation verification

**Scope**
- Retrieve BC legislation only from official BC Laws sources; version source text with URL, retrieval time, effective dates, and hash.
- Verify provision existence, pinpoint, quotation, currency, and proposition fit.
- Separate case citation identity from good-law/treatment status; never claim automated treatment completeness without an approved source.
- Keep `court_ready=false` unless all required checks and human review pass.

**Acceptance**
- [ ] RTA/JRPA/ATA fixtures validate correct and incorrect sections/quotes.
- [ ] Point-in-time and amended/repealed fixtures return explicit currency results.
- [ ] Source outage or uncertainty fails closed and is audited.
- [ ] No CanLII legislation is presented as the official statutory source.

### P0-15 — Repair Hugging Face model packaging

**Scope**
- Classify repository as checkpoint, adapter, or documentation/policy artifact.
- Supply valid upstream/base-model metadata and loading instructions; remove misleading custom architecture identity.

**Acceptance**
- [ ] Artifact loads through its documented Transformers class without `trust_remote_code=True`, or clearly declares that no weights are provided.
- [ ] Model card accurately states capabilities, limitations, privacy restrictions, and evaluation status.

### P0-16 — Add security telemetry, backup, and recovery

**Scope**
- Instrument auth failures, authorization denials, quarantine events, audit-chain failures, queue failures, citation degradation, and privileged exports without logging client content/secrets.
- Add encrypted PostgreSQL/MinIO backups, retention, restore runbook, and recovery objectives.

**Acceptance**
- [ ] Synthetic incidents trigger actionable alerts with correlation IDs.
- [ ] Restore drill rebuilds database plus referenced evidence and verifies hashes/audit chain.
- [ ] Logs demonstrate tenant-safe redaction and access controls.

### P0-17 — Execute Gate 0 adversarial release suite

**Scope**
- Run cross-org/matter IDOR, ethical-wall, CSRF/session, upload/parser, SQL, audit concurrency, queue concurrency, restart, backup/restore, citation fail-closed, and court-ready bypass tests.
- Produce a signed evidence index mapping every Gate 0 criterion to automated result or approved manual review.

**Acceptance**
- [ ] Zero open critical/high findings and no unexplained route-matrix gaps.
- [ ] All P0 acceptance criteria have reproducible evidence.
- [ ] Security, engineering, legal-content, privacy, and operations owners sign Gate 0.

## Delivery sequence

1. **Foundation:** P0-01, P0-02, P0-15.
2. **Isolation and access:** P0-03, P0-04, P0-05.
3. **Integrity and ingestion:** P0-06, P0-07, P0-08, P0-09.
4. **Durable workflows:** P0-10, P0-11, P0-12, P0-13.
5. **Legal verification and operations:** P0-14, P0-16.
6. **Release decision:** P0-17.

## Gate 0 definition of done

- [ ] Production runs on PostgreSQL with tested RLS and least-privilege roles.
- [ ] Every protected operation has authentication, object authorization, CSRF where applicable, and audit coverage.
- [ ] Evidence is quarantined, malware-scanned, immutable, encrypted, and inaccessible before release.
- [ ] HITL, post-resolution, jobs, and audit integrity survive restarts and concurrency.
- [ ] Citations fail closed and source official legislation correctly.
- [ ] Backup restoration and adversarial release tests pass.
- [ ] The system remains labelled Internal Alpha until the signed Gate 0 report is approved.
