# SQLite to PostgreSQL Migration Plan

**Baseline:** 2026-07-23 repository state  
**Production target:** PostgreSQL 16 (`pgvector/pgvector:pg16` currently declared)  
**Development compatibility:** SQLite may remain for fast local/unit tests, but is not a production authority.  
**Related controls:** P0-01, P0-02, P0-03, P0-06, P0-10–13, P0-16, P0-17 in `P0_ENGINEERING_BACKLOG.md`.

## 1. Decision and success criteria

PostgreSQL becomes the sole production system of record. Migration is complete only when:

- one versioned schema authority creates and upgrades all runtime tables;
- application services pass PostgreSQL integration tests without SQL rewriting at runtime;
- all tenant-owned data is constrained by organization/matter relationships and FORCE RLS;
- workflow, audit, and job concurrency use PostgreSQL transactions correctly;
- SQLite data can be exported, transformed, loaded, reconciled, and rolled back through a rehearsed runbook;
- backup/restore and post-cutover monitoring pass; and
- production cannot silently fall back to SQLite.

## 2. Repository baseline and blocking findings

### Current connection/migration behavior

- `backend/db/connection.py` selects PostgreSQL only when `ALA_POSTGRES_URL` is set; otherwise it silently selects SQLite at `data/ala_platform.sqlite3`.
- It opens a new connection per context and commits/rolls back, but no production connection pool, statement timeout, transaction isolation policy, or transaction-local tenant context is configured.
- `backend/db/migrate.py` maintains a SQLite-only `schema_migrations` record. The PostgreSQL path executes `phase3_core.sql` and `m1_platform.sql` by naive `sql.split(";")` and has no durable migration version/checksum history.
- `docker-compose.yml` also initializes `v1_data_model.sql`, creating a competing schema authority before application startup.

### Competing schemas

Three PostgreSQL contracts overlap but do not describe one compatible model:

1. `phase3_core.sql`: Phase 3 matters, consent, exceptions, production, legal knowledge.
2. `m1_platform.sql`: organizations, users, sessions, memberships, conflict, audit, evidence, tests.
3. `v1_data_model.sql`: a broader enterprise schema with alternate table names and shapes (`evidence_documents`, `consent_records`, `audit_entries`, `conversations`, etc.).

Examples of conflict:

- `phase3_core.sql` creates `matters(matter_id,title,created_at)` before `m1_platform.sql` tries to extend it; `v1_data_model.sql` defines a different richer matter model.
- `users`, `sessions`, `matters`, consent, evidence, conversations, and audit have overlapping names or concepts with different columns/types.
- Runtime SQLite tables use `documents`, `consents`, `audit_ledger`, `workspace_conversations`, and separate service-created `conversations`/`chat_messages`/`background_jobs`.

**Decision:** adopt the currently exercised modular-monolith runtime tables as the migration source model. Treat `v1_data_model.sql` as a future-domain design reference, not an entrypoint schema. Port future entities through explicit versioned migrations rather than loading that file automatically.

### SQL compatibility defects

Repository search shows positional `?` parameters throughout identity, matters, workspace, conversations, consent, conflicts, evidence, export, citations, audit, and jobs. Psycopg 3 expects `%s` positional placeholders. `backend/db/helpers.py` describes a future compatibility function but does not implement one. Dynamic IN placeholders in `export_manifest.py` are also SQLite-shaped.

Other defects:

- `audit_ledger.seq INTEGER PRIMARY KEY AUTOINCREMENT` is SQLite-only in `SQLITE_CREATE_TABLES`; PostgreSQL contract uses `bigserial`.
- SQLite stores timestamps and JSON as `TEXT`, and booleans as `INTEGER`; PostgreSQL contracts use `timestamptz`, `jsonb`, and `boolean`.
- `compat_schema_ddl()` naively splits semicolons and replaces time defaults with empty strings; it must not be used as a production migration parser.
- Jobs and conversation services create tables at service runtime, bypassing central migration ownership.
- PostgreSQL contracts omit several currently used runtime tables: citation verification/audit, export manifests, workspace persistence, service conversations/messages, and background jobs.

## 3. Target database architecture

### Tooling

Use **Alembic with SQLAlchemy 2.x Core** for versioned DDL and database-neutral service queries. A thin psycopg repository is acceptable only if it centralizes parameter binding and dialect-specific operations; raw `?`-to-`%s` string replacement is not acceptable because SQL literals/operators can be corrupted and complex queries remain untested.

### Runtime topology

- PostgreSQL 16 with TLS, private network, encrypted storage, automated backups, and point-in-time recovery.
- SQLAlchemy pooled connections with bounded pool/overflow, `pool_pre_ping`, statement/lock/idle transaction timeouts, application name, and metrics.
- Separate roles:
  - `ala_migrator`: owns schema and runs migrations; no application traffic.
  - `ala_runtime`: CRUD through RLS; cannot alter schema or disable RLS.
  - `ala_audit_writer`: insert/select required audit functions only; no update/delete/truncate.
  - `ala_readonly`/support: narrowly scoped views, time-bound access, audited.
- Production startup checks migration head and fails if absent/outdated. It never auto-runs DDL under the runtime role.

### Transaction tenant context

At transaction start, the trusted server sets transaction-local context after authentication:

```sql
SET LOCAL app.org_id = '<validated org id>';
SET LOCAL app.user_id = '<validated user id>';
```

RLS policies reference `current_setting('app.org_id', true)` and deny when missing. Clients never submit or directly set trusted organization context. Pooled connections must use `SET LOCAL`, not persistent `SET`, and tests must prove no context leakage.

### Canonical type mapping

| SQLite source | PostgreSQL target | Transform/validation |
|---|---|---|
| `TEXT` ID | `text` initially | Preserve existing IDs; UUID conversion can be a later explicit migration |
| ISO timestamp `TEXT` | `timestamptz` | Parse as UTC; reject/triage malformed or timezone-free values |
| JSON `TEXT` | `jsonb` | Parse strictly; canonicalize; quarantine invalid JSON rather than silently coercing |
| Boolean `INTEGER` | `boolean` | Accept only 0/1/null according to target nullability |
| `INTEGER` sizes/sequence | `bigint`; identity for sequence | Validate nonnegative sizes; set sequence after load |
| `REAL` confidence | `double precision` or `real` | Validate expected range where applicable |
| Dynamic empty strings | nullable or constrained `text` | Preserve only where semantically meaningful; do not convert IDs to null silently |

## 4. Canonical schema inventory

### Runtime tables to migrate

| Domain | SQLite/runtime source | PostgreSQL target action |
|---|---|---|
| Migration | `schema_migrations` | Replace with Alembic version table plus optional checksum/deployment ledger |
| Identity | `organizations`, `users`, `sessions` | Canonicalize timestamps/booleans; index org/user/session expiry; RLS where appropriate |
| Matters | `matters`, `matter_members` | Make `org_id` non-null after backfill; constraints and deny-first membership semantics |
| Conflict | `parties`, `matter_parties`, `conflict_checks` | JSONB aliases/addresses/hits; org/matter RLS |
| Audit | `audit_ledger` | `bigint GENERATED ... AS IDENTITY`; serialized chain-head table; append-only grants |
| Consent | `consents` | JSONB processing scope; tenant columns/version/idempotency; preserve withdrawal history |
| Evidence | `documents`, `document_pages`, `propositions`, `evidence_relationships` | types/FKs; org/matter RLS; quarantine evolution through separate migration |
| Knowledge | `knowledge_sources`, `legal_test_registry` | JSONB and booleans; source/version constraints |
| Citation | `citation_verifications`, `citation_audit_events` | Add explicit `org_id`; JSONB reasons/detail; RLS |
| Export | `export_manifests` | Add explicit `org_id`, versions; JSONB fields; approvals later normalized to events |
| Workspace | `workspace_conversations`, `workspace_messages` | Retain if API uses this model; org/matter RLS and ownership constraints |
| Chat | `conversations`, `chat_messages` | Central migration; resolve overlap with workspace names; org/user/matter access indexes |
| Jobs | `background_jobs` | Central migration; leases/retries/idempotency/DLQ fields; org/matter ownership as needed |

### New P0 persistence tables

Create in ordered migrations rather than copying in-memory objects:

- HITL: exceptions, escalation tickets, production packages, approval records, workflow outbox.
- Post-resolution: outcomes, obligations/compliance events, escalations, JR clocks/petitions, stay/enforcement packages, retention closures.
- Evidence: quarantine transitions and page/span release state.
- Audit: chain heads and signed checkpoints.
- Operations: idempotency records if not domain-local.

Every tenant-owned table must have a non-null `org_id`; matter-owned rows must have a validated `matter_id` foreign key. Prefer composite uniqueness/foreign-key constraints where they prevent cross-tenant parent/child links.

## 5. Migration phases

### Phase 0 — Freeze and inventory

**Actions**

1. Stop ad-hoc schema additions while canonical model is finalized.
2. Record every SQLite file path/environment in use, file size, SHA-256, SQLite version, journal mode, and application build.
3. Run `PRAGMA integrity_check`, `foreign_key_check`, table/index inventory, row counts, null/orphan/duplicate scans, JSON parse checks, timestamp parse checks, and audit-chain verification.
4. Inventory filesystem evidence objects and reconcile every `storage_uri`, size, and SHA-256.
5. Classify the database as synthetic-only or containing live/confidential data; apply encrypted handling and chain-of-custody accordingly.

**Exit:** signed inventory and anomaly report; unresolved corruption has an explicit disposition.

### Phase 1 — Establish one schema authority

**Actions**

1. Add Alembic and SQLAlchemy dependencies and configuration.
2. Generate a reviewed baseline migration for the canonical modular-monolith tables.
3. Remove `v1_data_model.sql` from Docker automatic initialization. Archive/reference it without executing it.
4. Stop `backend/db/migrate.py` from splitting PostgreSQL SQL files. Retain a controlled SQLite test schema temporarily or generate both schemas from shared metadata.
5. Move `background_jobs`, `conversations`, and `chat_messages` DDL from service modules into migrations.
6. Configure production to check—not mutate—schema at startup.

**Exit:** empty PostgreSQL upgrades to head; repeated upgrade is safe; prior schema snapshot upgrade and downgrade/restore rehearsal pass.

### Phase 2 — Refactor application persistence

**Actions**

1. Replace direct DB-API SQL in services with SQLAlchemy Core repositories and named bound parameters.
2. Standardize row mapping, UTC datetimes, JSON objects, booleans, transaction boundaries, unique-violation handling, and pagination.
3. Add explicit transaction APIs for multi-step workflow/audit/outbox operations.
4. Add PostgreSQL-native code paths only where needed:
   - `FOR UPDATE`/`SKIP LOCKED` for jobs and clocks;
   - serialized audit chain head;
   - JSONB operations;
   - RLS context.
5. Add a production guard: `APP_MODE=production` requires PostgreSQL and refuses `ALA_SQLITE_PATH` fallback.

**Exit:** dual-backend contract tests pass for supported local behavior; all production/concurrency tests run against PostgreSQL.

### Phase 3 — Add tenant constraints, RLS, and roles

**Actions**

1. Add nullable `org_id` columns to tenant-owned legacy tables in an expand migration.
2. Backfill from matter/parent relationships; produce a quarantine report for ambiguous/unowned rows.
3. Add indexes, validated foreign keys, and then `NOT NULL` constraints.
4. Enable and FORCE RLS. Add select/insert/update/delete policies scoped by organization; supplement with matter membership where database policy design supports it.
5. Create least-privilege roles and revoke `PUBLIC` schema/table privileges.
6. Add append-only audit grants and prohibit runtime schema ownership.

**Exit:** direct SQL and API cross-org tests fail; pool reuse does not leak context; runtime cannot bypass/disable RLS.

### Phase 4 — Build extraction and load tooling

Use a repository script that reads SQLite in a consistent snapshot and writes PostgreSQL through explicit typed mappings. Do not use loose CSV as the only migration path for JSON/timestamps/legal text.

**Extraction rules**

- Open SQLite read-only after backup; use a transaction/snapshot or application write freeze.
- Export tables in dependency order with source PK, transformed row, and per-row canonical hash.
- Stream in batches; never log sensitive field values.
- Preserve original IDs, timestamps, hashes, statuses, and audit sequence.

**Load order**

1. organizations
2. users, sessions
3. matters, matter_members
4. parties, matter_parties, conflict_checks
5. documents, document_pages, propositions, relationships
6. consents and legal/HITL data
7. knowledge and legal test data
8. citations and citation audit
9. conversations/messages and workspace data
10. exports, jobs, post-resolution state
11. audit ledger last, preserving sequence and re-verifying chain

Use `COPY` into staging tables for volume, then validated `INSERT ... SELECT` into canonical tables. Staging tables are access-restricted and dropped after approval.

**Sequence handling**

After preserving audit `seq`, set its identity sequence to at least `MAX(seq)` before allowing new writes. Do not renumber audit entries.

**Exit:** dry-run load is repeatable; transformation rejects are explicit and zero unexplained rows are dropped.

### Phase 5 — Reconciliation and acceptance

For each table compare:

- source/extracted/loaded row counts;
- primary-key sets;
- canonical per-row hashes and aggregate hash manifests;
- null/status/timestamp distributions;
- foreign-key orphans and duplicate unique keys;
- JSON semantic equality;
- earliest/latest timestamps;
- organization/matter ownership coverage.

Domain checks:

- every session references a valid user/organization and preserves expiry/revocation;
- every matter member references the same authorized organizational model;
- evidence file bytes, size, database SHA-256, storage object, and page hashes reconcile;
- audit sequence is continuous as expected and `verify_chain()` passes end-to-end;
- consent status/history is preserved; withdrawal is never converted to deletion;
- citation/export/conversation counts and child relationships match;
- no active object points to a missing filesystem/MinIO object.

**Exit:** reconciliation report signed by database, application, security/privacy, and legal-workflow owners.

### Phase 6 — Cutover

#### Preferred initial cutover: planned write freeze

Given Internal Alpha status and unresolved concurrency/persistence work, use a simple, safer maintenance cutover rather than dual writes.

1. Announce maintenance and stop workers/background jobs.
2. Disable writes at ingress; allow active requests to drain.
3. Create encrypted SQLite and evidence snapshots; record hashes.
4. Run final integrity/audit/object reconciliation.
5. Extract and load final delta/full snapshot.
6. Run schema, row/hash, RLS, auth, evidence, workflow, queue, and smoke tests.
7. Set production secret `ALA_POSTGRES_URL`; deploy application with SQLite fallback disabled.
8. Start one canary API/worker, then expand gradually while monitoring.
9. Keep SQLite mounted read-only and inaccessible to application writes.

**Estimated outage:** determine from a production-sized rehearsal; do not promise a duration before measured extraction/load/index time is known.

#### Later near-zero-downtime option

Only if scale requires it: add an application outbox/change log, bulk-load a snapshot, replay ordered changes idempotently, briefly freeze writes, reconcile, and switch. Avoid uncontrolled dual writes because divergent legal/audit state is harder to prove and roll back.

### Phase 7 — Observation and decommission

1. Maintain a defined observation window with heightened auth denial, DB error, latency, deadlock, pool, RLS, audit, job, and object-reference alerts.
2. Take immediate PostgreSQL backup and perform a restore rehearsal.
3. After sign-off, securely archive encrypted SQLite snapshots under legal retention policy; do not casually delete evidence of migration.
4. Remove SQLite write dependencies from production deployment and docs.
5. SQLite may remain only in explicitly labeled test/development profiles.

## 6. Rollback plan

### Rollback triggers

- reconciliation mismatch or missing/changed evidence;
- audit-chain verification failure;
- cross-tenant/RLS failure;
- material authorization regression;
- unacceptable DB error/latency/deadlock rate;
- workflow/job duplicate or lost state;
- restore/backup failure.

### Safe rollback before PostgreSQL writes

Redirect application to the untouched read-only snapshot copy only after restoring a writable copy from the pre-cutover SQLite backup, validating its hash/integrity, and redeploying the previous compatible application build.

### Rollback after PostgreSQL writes

Do **not** simply point back to stale SQLite. That would lose or fork legal records, approvals, audit events, and evidence references. Choose one rehearsed path:

1. repair-forward in PostgreSQL while writes remain paused; or
2. export the bounded PostgreSQL post-cutover delta through a reviewed reverse transformer, apply it to a restored SQLite copy in sequence, reconcile everything, then switch.

If neither is proven safe, remain read-only and invoke incident/change control. Preserve both stores and all manifests for investigation.

### Point of no return

After contract migrations remove legacy columns or after sustained PostgreSQL writes without a tested reverse path, rollback is restore/repair—not a configuration flip. Contract migrations occur only after the observation window and formal approval.

## 7. Test plan

### Schema and compatibility

- Empty-to-head, previous-to-head, downgrade/restore, checksum drift, concurrent startup, and unsupported-version tests.
- CRUD contract tests on SQLite and PostgreSQL for identity, matters, conflicts, consent, evidence, citations, exports, workspace, conversations, audit, and jobs.
- Static CI rule rejects raw SQLite-only SQL outside approved adapter/test migration files.

### PostgreSQL-only correctness

- 100 concurrent audit appends.
- Competing job/JR clock workers with leases and crash recovery.
- Optimistic workflow transitions and idempotency replay.
- Unique/FK/check constraint behavior.
- Transaction rollback and outbox atomicity.
- Deadlock/serialization retry policy.

### Security and isolation

- RLS on every tenant table with cross-org, cross-matter, revoked, and ethical-wall principals.
- Runtime role cannot alter schema, disable RLS, or mutate audit history.
- Tenant context absent/invalid fails closed; pooled connection reuse remains isolated.
- Backup/staging/migration logs do not expose client content or credentials.

### Performance and operations

- Production-sized load rehearsal with measured downtime.
- Critical query `EXPLAIN (ANALYZE, BUFFERS)` and index validation.
- Pool exhaustion, statement timeout, lock timeout, restart, failover, backup, PITR, and restore tests.

## 8. Observability and runbook evidence

Monitor and alert on:

- connection-pool usage/waits, transaction duration, idle-in-transaction sessions;
- query latency/error rates, deadlocks, lock waits, statement timeouts;
- migration version drift;
- RLS/authorization denials by safe metadata only;
- audit append/checkpoint failures;
- job lease/retry/DLQ counts;
- row/object reconciliation failures;
- backup age, WAL/PITR health, restore test age, disk growth.

Cutover evidence package:

- source database/evidence snapshot hashes;
- integrity and anomaly reports;
- migration version/checksums;
- extraction/load manifests and rejected-row report;
- per-table reconciliation and domain invariant results;
- audit-chain and object-hash verification;
- RLS/authorization/concurrency/smoke test outputs;
- backup/restore proof;
- go/no-go and rollback authority signatures.

## 9. Ownership and sequencing

| Work | Accountable owner | Required reviewers |
|---|---|---|
| Canonical schema and migrations | Database/backend lead | security, application owners |
| Data mapping and reconciliation | Data/database engineer | legal-workflow owner, privacy |
| RLS and roles | Security/database lead | identity/application owner |
| Audit migration | Security/audit owner | database lead |
| Evidence/object reconciliation | Evidence platform owner | security/privacy |
| Cutover/rollback | SRE/release manager | all above; product/legal operations |

Recommended sequence aligns with the backlog:

1. P0-01 migration authority.
2. P0-02 persistence refactor.
3. P0-03 tenant/RLS roles.
4. P0-06 audit concurrency before importing active audit writes.
5. P0-10–13 durable workflows/jobs.
6. P0-16 backup/recovery.
7. P0-17 migration-inclusive release gate.

## 10. Go/no-go checklist

### Go

- [ ] Canonical schema conflict is resolved and automatic `v1_data_model.sql` initialization removed.
- [ ] PostgreSQL migration runner is versioned, transactional, and at expected head.
- [ ] Production SQLite fallback is impossible.
- [ ] All data/object/audit reconciliation checks pass with zero unexplained loss.
- [ ] RLS, role, route authorization, concurrency, and restart tests pass.
- [ ] Backups and restore drill pass.
- [ ] Measured performance meets approved thresholds.
- [ ] Rollback authority and runbook are staffed for the observation window.

### No-go

Any unexplained row/hash mismatch, audit failure, orphan evidence object, RLS bypass, authorization gap, failed restore, duplicate consequential job, lost workflow state, or silent fallback is an automatic no-go.
