# P0 Engineering Backlog — Production Remediation

**Generated from:** Production Readiness Audit 2026-07-22  
**Repository code analysis completed:** 2026-07-23  
**Assessment:** 8 of 17 findings were already remediated; 9 remain broken or incomplete.

---

## Status Legend

| Icon | Meaning |
|------|---------|
| ✅ | Already remediated in codebase |
| ❌ | Still broken — needs work |
| ⏳ | Partially addressed — needs follow-up |

---

## Workstream 1: PostgreSQL Compatibility (Finding 1)

**Status:** ❌ Still broken

**Files identified with SQLite-specific SQL:**

| File | Pattern | Risk |
|------|---------|------|
| `backend/platform/jobs.py` | `executescript()`, `datetime('now')` | Schema creation and timestamps break on PostgreSQL |
| `backend/platform/consent_store.py` | `datetime('now')` | INSERT timestamp fails on PostgreSQL |
| `backend/audit/ledger.py` | Implicit SQLite autoincrement via `seq` column | PostgreSQL uses SERIAL/IDENTITY |
| `backend/identity/service.py` | `ON CONFLICT ... DO UPDATE SET` (PostgreSQL-compatible) | ✅ OK |
| `backend/platform/conflicts.py` | `INSERT OR IGNORE` (PostgreSQL: `ON CONFLICT DO NOTHING`) | ⏳ Fixed in migrate.py, not in conflicts.py |
| `backend/platform/citations.py` | `?` parameter style (SQLite default) | Needs `%s` for psycopg |

### Task P0-01: Remove SQLite-specific SQL from all backend service files

**Files to edit:**
- `backend/platform/jobs.py` — Replace `executescript()` with individual statements; replace `datetime('now')` with parameterized ISO timestamp
- `backend/platform/consent_store.py` — Replace `datetime('now')` with parameterized timestamp
- `backend/platform/conflicts.py` — Replace `INSERT OR IGNORE` with `INSERT ... ON CONFLICT DO NOTHING`
- `backend/platform/citations.py` — Replace `?` placeholders with DB-agnostic parameter style
- `backend/db/migrate.py` — ✅ Already fixed (uses parameterized timestamps and `SELECT ... WHERE NOT EXISTS`)

### Task P0-02: Add DB-agnostic parameter helper

- Create `backend/db/helpers.py` with parameter style detection (`%s` for psycopg, `?` for sqlite3)
- Or migrate all files to use SQLAlchemy 2.x Core expressions

### Acceptance Criteria
- [ ] All 5 service files pass unit tests against both SQLite and PostgreSQL
- [ ] Docker Compose with `ALA_POSTGRES_URL` set starts successfully and all CRUD operations work
- [ ] No `datetime('now')`, `executescript()`, `INSERT OR REPLACE`, `INSERT OR IGNORE`, or `?` placeholders in backend service files

---

## Workstream 2: Evidence Quarantine State Machine (Finding 5)

**Status:** ❌ Still broken

**Current behavior:** Bytes written to disk first; only filename extension check; status set to `BLOCKED` or `CLEAN`.

**Required:** `RECEIVED → QUARANTINED → TYPE_VALIDATED → MALWARE_SCANNED → EXTRACTED → HUMAN_REVIEWED → RELEASED`

### Task P0-03: Implement proper quarantine state machine

**File to create/edit:** `backend/platform/evidence.py`

**Required changes:**
1. Define quarantine state enum: `RECEIVED`, `QUARANTINED`, `TYPE_VALIDATED`, `MALWARE_SCANNED`, `EXTRACTED`, `HUMAN_REVIEWED`, `RELEASED`
2. Write bytes to a `QUARANTINED` directory (not directly to object store)
3. Implement magic-byte MIME detection (use `python-magic` or `puremagic`)
4. Block executables, archives with nested executable content, and polyglot files at `TYPE_VALIDATED` stage
5. Implement malware scanning hook (local ClamAV or stub with explicit documentation that real AV is required)
6. Add page/span-level quarantine status column to `document_pages` table
7. Add `quarantine_state` column with transitions table
8. Audit all quarantine transitions

### Acceptance Criteria
- [ ] Uploaded files start as `RECEIVED` and transition through all 7 states
- [ ] Extension-only check is replaced with magic-byte MIME detection
- [ ] Malicious PDFs, scripts with misleading extensions, and polyglot files are detected at `TYPE_VALIDATED`
- [ ] All quarantine transitions are logged to the audit ledger
- [ ] Files are not accessible for processing until `RELEASED`

---

## Workstream 3: Persisted HITL and Post-Resolution State (Finding 6)

**Status:** ❌ Still broken

**Current behavior:** `backend/api/state.py` creates in-memory singleton `HitlControlPlane()` and `PostResolutionEngine()`.

**Impact:** State loss on restart, inconsistent across workers, no horizontal scaling.

### Task P0-04: Persist workflow state to PostgreSQL

**Sub-tasks:**
1. Create database tables for:
   - `hitl_consent_records` (mirroring `ConsentRecord` fields)
   - `hitl_exception_events` (mirroring `ExceptionEvent` fields)
   - `hitl_exception_tickets` (mirroring `EscalationTicket`)
   - `hitl_production_packages` (mirroring `ProductionPackage`)
   - `hitl_approval_records` (mirroring approval events)
   - `post_resolution_outcomes` (mirroring `OutcomeRecord`)
   - `post_resolution_compliance_ledger`
   - `post_resolution_escalation_tickets`
   - `post_resolution_jr_clocks`
2. Add version columns and idempotency keys to each table
3. Implement transactional outbox pattern for audit events
4. Add `FOR UPDATE SKIP LOCKED` for JR clock processing

### Acceptance Criteria
- [ ] HITL consent grants survive application restart
- [ ] Exception emissions survive restart
- [ ] Production freeze/review/approve/release state survives restart
- [ ] Post-resolution outcomes survive restart
- [ ] Workflow state is consistent across 3+ concurrent workers
- [ ] Idempotency keys prevent duplicate consent grants and exception emissions

---

## Workstream 4: Audit Chain Concurrency Safety (Finding 7)

**Status:** ❌ Still broken

**Current behavior:** `audit/ledger.py` reads latest hash, then inserts — no lock on chain head.

### Task P0-05: Serialize audit appends

**Required changes in `backend/audit/ledger.py`:**
1. For PostgreSQL: Use `SELECT ... FOR UPDATE` on the latest chain head record (or advisory lock `pg_advisory_xact_lock`)
2. For SQLite: Use `BEGIN IMMEDIATE` transaction with `SELECT ... FOR UPDATE` (or table-level lock via `INSERT ... SELECT` in a single statement)
3. Compute the new hash within the locked transaction
4. Default verification beyond 10,000 entries should accept a `limit` parameter instead of hard-coded limit

### Task P0-06: Add append-only database permissions

- Add DB migration that creates a restricted role with only `INSERT` on `audit_ledger` (no `UPDATE`, `DELETE`, `TRUNCATE`)
- Application connects with this restricted role for audit operations
- Admin functions use a separate connection with full permissions

### Task P0-07: Externally anchor checkpoint hashes

- Implement periodic checkpoint generation (every N entries or time-based)
- Sign checkpoint hash with a key
- Store signed checkpoints (optionally publish to public log or separate storage)

### Acceptance Criteria
- [ ] 100 concurrent audit append requests produce a valid chain (verified)
- [ ] No two requests can calculate the same predecessor hash
- [ ] No `UPDATE` or `DELETE` operations are permitted on `audit_ledger` via the application connection
- [ ] Signed checkpoints can be verified independently
- [ ] Chain verification works for any range (not limited to 10,000)

---

## Workstream 5: Secure Browser Session Tokens (Finding 8)

**Status:** ❌ Still broken

**Current behavior:** `frontend/client/app.js` stores token in `localStorage` (XSS-accessible). Logout does not call backend revocation endpoint.

### Task P0-08: Replace localStorage with Secure+HttpOnly cookies

**Required changes:**

**Backend (`backend/api/main.py` and `backend/identity/service.py`):**
1. Add session cookie endpoints: `/v1/platform/auth/session/login` returns cookie, `/v1/platform/auth/session/logout` clears it
2. Cookie attributes: `Secure`, `HttpOnly`, `SameSite=Strict`, `Path=/`
3. CSRF token generation endpoint and double-submit cookie pattern
4. Access token rotation (short-lived access + long-lived refresh)

**Frontend (`frontend/client/app.js`):**
1. Remove all `localStorage` token storage
2. Use `fetch` with `credentials: 'include'` for cookie-based auth
3. Add CSRF token header to mutation requests (POST, PUT, PATCH, DELETE)
4. Implement refresh token rotation

### Task P0-09: Implement server-side session revocation on logout

**Backend:**
1. `/v1/platform/auth/logout` already exists and calls `revoke_session()` — verify it's called from the frontend
2. Add session revocation for logout across all auth methods

**Frontend:**
1. Logout button must call `POST /v1/platform/auth/logout` before clearing any local state

### Task P0-10: Add Content Security Policy headers

- Add `Content-Security-Policy` header in `backend/api/main.py`
- Restrict: `default-src 'self'`, `script-src 'self'`, `style-src 'self' 'unsafe-inline'`, `connect-src 'self'`
- Add report-uri for CSP violation reporting

### Acceptance Criteria
- [ ] No bearer token is stored in `localStorage` or `sessionStorage`
- [ ] All authenticated requests use `Secure` + `HttpOnly` + `SameSite=Strict` cookies
- [ ] CSRF protection is enforced on all state-changing requests
- [ ] Logout revokes the server session AND clears the cookie
- [ ] CSP headers are applied and tested
- [ ] Access token rotation works correctly

---

## Workstream 6: Redis and MinIO Integration (Finding 12)

**Status:** ❌ Still broken

**Current behavior:** Docker Compose starts Redis and MinIO, but evidence uses `data/object_store/` filesystem and jobs use SQLite queue.

### Task P0-11: Implement MinIO/S3-compatible object storage for evidence

**Required changes in `backend/platform/evidence.py`:**
1. Add `boto3` dependency (or `s3fs`) for S3-compatible storage
2. On service init, check for `ALA_S3_ENDPOINT` env var
3. If set, use S3/MinIO client; otherwise fall back to filesystem
4. Upload files to `s3://ala-evidence/{org_id}/{matter_id}/{document_id}.bin`
5. Generate pre-signed URLs for access (signed access URLs, not direct file reads)
6. Ensure immutable object storage (versioning enabled, no overwrites)

### Task P0-12: Implement Redis-based durable job queue

**Required changes in `backend/platform/jobs.py`:**
1. Add `redis` dependency
2. On service init, check for `ALA_REDIS_URL` env var
3. Replace SQLite `background_jobs` table with Redis lists/streams
4. Implement: `enqueue` → Redis `RPUSH`, `run_next` → `BLPOP` with timeout
5. Add job leases (prevent double-execution on worker crash)
6. Add dead-letter queue for failed jobs
7. Implement idempotent job handlers

### Acceptance Criteria
- [ ] Evidence files are stored in MinIO when `ALA_S3_ENDPOINT` is set
- [ ] Evidence files are stored on filesystem when `ALA_S3_ENDPOINT` is not set
- [ ] Files are accessible only via signed URLs
- [ ] Jobs are processed via Redis when `ALA_REDIS_URL` is set
- [ ] Job queue survives worker restarts (leases)
- [ ] No job is executed more than once (atomic claim)
- [ ] Failed jobs go to dead-letter queue

---

## Workstream 7: Job Queue Concurrency Safety (Finding 13)

**Status:** ❌ Still broken

**Current behavior:** `jobs.py` selects oldest `PENDING` row, then updates — no atomic claim.

### Task P0-13: Implement atomic job claim

**Option A (PostgreSQL):** Use `FOR UPDATE SKIP LOCKED`
```sql
UPDATE background_jobs
SET status = 'RUNNING', started_at = NOW()
WHERE job_id = (
    SELECT job_id FROM background_jobs
    WHERE status = 'PENDING'
    ORDER BY created_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED
)
RETURNING *;
```

**Option B (SQLite):** Use `BEGIN IMMEDIATE` with row-level lock simulation

**Option C (Redis):** Use atomic `RPOPLPUSH` or Redis streams with consumer groups

### Task P0-14: Add job leases, retries, and dead-letter handling

- Add `leased_until` column (timestamp after which another worker can reclaim)
- Add `retry_count` and `max_retries` columns
- Add `dead_letter_at` column for jobs exceeding max retries
- Add idempotency keys: `job_type + payload_hash` unique constraint prevents duplicate enqueue

### Acceptance Criteria
- [ ] Two concurrent workers never claim the same job
- [ ] Worker crash during job execution releases the job (via lease expiry)
- [ ] Job is retried up to `max_retries` times
- [ ] Job exceeding max retries moves to dead-letter queue
- [ ] No duplicate job is created for the same work (idempotency)

---

## Workstream 8: Citation Verification Expansion (Finding 15)

**Status:** ❌ Still broken

**Current behavior:** Keyword matching against 3 known statute identifiers. No section retrieval, pinpoint validation, quotation verification, or currency checking.

### Task P0-15: Expand citation verification to real verification

**Required changes in `knowledgebase/citation_verifier/` and `backend/platform/citations.py`:**
1. Add BC Laws API integration for section retrieval
2. Implement pinpoint validation: verify quoted text matches actual section text
3. Implement quotation verification: hash comparison between quoted text and source
4. Implement currency checking: compare citation date against effective/amended dates
5. Implement case treatment checking: verify case is still good law (not overturned/overruled)
6. Update `court_ready` to reflect actual verification status (not always false)

### Acceptance Criteria
- [ ] Citations to RTA, JRPA, ATA retrieve the actual section text from BC Laws
- [ ] Pinpoint validation confirms the section exists and the quotation is accurate
- [ ] Currency checking confirms the cited version is still in force
- [ ] Case treatment checking confirms the case is still good law
- [ ] `court_ready` is `true` only when full verification passes
- [ ] All verification steps are audited

---

## Workstream 9: CORS Hardening Verification (Finding 9)

**Status:** ✅ Already remediated

Code in `backend/api/main.py`:
```python
def _cors_origins() -> list[str]:
    mode = os.environ.get("APP_MODE", "development").strip().lower()
    if mode == "development":
        return ["*"]
    raw = os.environ.get("CORS_ORIGINS", "").strip()
    ...
if len(_cors) == 1 and _cors[0] == "*" and _mode != "development":
    raise RuntimeError(...)
```

**No additional work needed.**

---

## Workstream 10: Health Check Truthfulness (Finding 10)

**Status:** ✅ Already remediated

Code in `backend/api/main.py`:
- `/health/live` returns `{"status": "ok"}`
- `/health/ready` checks database + deployment safety and returns `"unhealthy"` with issues list

**No additional work needed.**

---

## Workstream 11: CI/Docker Consistency (Finding 11)

**Status:** ✅ Already remediated

Dockerfile installs with `pip install --no-cache-dir -e ".[dev,postgres,pdf,ocr]"` matching `pyproject.toml`.

**No additional work needed.**

---

## Workstream 12: Deadline Confirmation Fix (Finding 14)

**Status:** ✅ Already remediated

Both `/v1/platform/deadlines/calculate` and `/v1/deadlines/calculate` force `human_confirmed=False`. Deadline confirmation requires separate authenticated approval event.

**No additional work needed.**

---

## Workstream 13: Drafting Error Handling (Finding 16)

**Status:** ✅ Already remediated

`backend/platform/drafting.py` returns explicit `"status": "degraded"` or `"status": "error"` states instead of success-shaped fallbacks.

**No additional work needed.**

---

## Workstream 14: Ethical Wall Deny-First (Finding 2)

**Status:** ✅ Already remediated

`backend/identity/service.py` `can_access_matter()` checks ethical wall BEFORE role-based access:
```python
if mem["access_level"] == "ethical_wall":
    return False  # Ethical wall blocks ALL roles, including owner/admin
if mem["revoked_at"] is not None:
    return False
if user.role in ("owner", "admin"):
    return True
```

**No additional work needed.**

---

## Workstream 15: API Security Model Consolidation (Finding 3)

**Status:** ✅ Already remediated

All routes in `backend/api/main.py` use `CurrentUser` dependency. All routes in `backend/api/platform_routes.py` use `CurrentUser` dependency. No caller-supplied actor identities.

**No additional work needed.**

---

## Workstream 16: Citation/Deadline Matter Authorization (Finding 4)

**Status:** ✅ Already remediated

`/v1/platform/citations/verify` validates matter access before verification.
`/v1/platform/deadlines/calculate` validates matter access before calculation.
Both write audit events with actor/org/matter metadata.

**No additional work needed.**

---

## Workstream 17: Hugging Face Model Repository (Finding 17)

**Status:** ❌ Not fully verified — needs codebase inspection

### Task P0-17: Audit and repair Hugging Face model repository

1. Check `huggingface/models/` and `huggingface/config/` for model identity
2. Ensure model is either a valid Qwen2 checkpoint or a documented reference to upstream Qwen2
3. Remove any `AutoModel` + `bc_legal_ai_policy_card` architecture identity
4. Add proper `config.json` with Qwen2 architecture if a real checkpoint is deployed

### Acceptance Criteria
- [ ] Model repository loads with `AutoModelForCausalLM` without `trust_remote_code=True`
- [ ] No "bc_legal_ai_policy_card" architecture string exists
- [ ] Model card accurately describes the model as a documentation/adapter repository, not a trained checkpoint

---

## Implementation Sequencing

### Phase 1 (Week 1-2): Critical P0 — 6 workstreams

```
Week 1:
  ├── P0-01: PostgreSQL compatibility (all 5 files)
  ├── P0-05: Audit chain serialization (lock chain head)
  ├── P0-08: Secure session cookies (backend)
  └── P0-13: Job queue atomic claim (SQLite first)

Week 2:
  ├── P0-03: Evidence quarantine state machine
  ├── P0-09: Server-side session revocation (frontend+backend)
  ├── P0-14: Job leases, retries, dead-letter
  └── P0-10: CSP headers
```

### Phase 2 (Week 3-4): P0 continued + integration tests

```
Week 3:
  ├── P0-04: Persist HITL state to DB
  ├── P0-06: Append-only audit permissions
  └── P0-07: Externally anchored checkpoints

Week 4:
  ├── P0-11: MinIO/S3 object storage
  ├── P0-12: Redis job queue
  ├── P0-15: Citation verification expansion (phase 1)
  └── P0-17: Hugging Face model repair
```

### Phase 3 (Week 5+): P0 completion + regression tests

```
Week 5+:
  ├── P0-15: Citation verification expansion (phase 2)
  ├── Integration tests for all P0 items
  ├── Concurrent worker tests (audit, jobs, state)
  └── Documentation updates
```

---

## Regression Test Requirements

For each P0 workstream, the following tests must pass:

1. **Unit tests** — All new functions have >80% coverage
2. **Integration tests** — Full workflows (e.g., upload → quarantine → scan → release)
3. **Concurrency tests** — 10+ concurrent requests for audit, jobs, and state
4. **Dual-backend tests** — All tests pass against both SQLite and PostgreSQL
5. **Security tests** — Unauthenticated access returns 401; unauthorized access returns 403

---

## Rollback Plan

Each P0 workstream should be reversible:

1. **Database migrations:** All schema changes must have a corresponding `DOWN` migration
2. **Feature flags:** New behaviors (e.g., Redis queue) should be behind env var feature flags
3. **Backward compatibility:** Old API contracts must be maintained during transition period (deprecation headers OK)

