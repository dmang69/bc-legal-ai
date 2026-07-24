# BC Legal AI — Repository-Grounded Security Threat Model

**Assessment baseline:** 2026-07-23 repository state  
**System classification:** Internal Alpha / prototype  
**Production decision:** No-go until Gate 0 in `P0_ENGINEERING_BACKLOG.md` passes  
**Method:** STRIDE-informed abuse-case analysis, adapted for confidential legal data, privilege, multi-tenancy, and AI output risks.

## 1. Scope and security objectives

### In scope

- FastAPI gateway: `backend/api/main.py`, `backend/api/platform_routes.py`, and dependencies.
- Identity/session layer: `backend/identity/`, `backend/api/dependencies.py`.
- Matter, conflict, consent, evidence, conversation, citation, drafting, export, HITL, post-resolution, audit, and job services.
- SQLite/PostgreSQL persistence in `backend/db/` and `architecture/contracts/sql/`.
- Browser client in `frontend/client/`.
- PostgreSQL, Redis, and MinIO declared in `docker-compose.yml`.
- Knowledge/citation sources and Hugging Face artifacts.

### Explicitly out of scope for current trust claims

- Public handling of live client files.
- A claim that current browser messaging is end-to-end encrypted.
- Autonomous filing, legal advice, or unsupervised court-ready output.
- Security guarantees from Redis/MinIO merely because containers are declared; application integration must be verified.

### Security objectives

1. **Confidentiality:** no cross-organization, cross-matter, ethical-wall, privilege, or public-demo leakage.
2. **Integrity:** preserve original evidence, provenance, workflow decisions, citations, deadlines, and audit order.
3. **Availability:** retain recoverable legal-work state and safely degrade when dependencies fail.
4. **Accountability:** authenticated actor, organization, matter, resource, decision, and timestamp for material actions.
5. **Human control:** no privileged, court-ready, deadline-confirmed, or externally consequential output bypasses required review.
6. **Source integrity:** legal propositions and citations remain tied to verified, current, authoritative sources.

## 2. Architecture and trust boundaries

```text
Untrusted browser/user
        |
        | HTTPS, cookies/bearer token, CSRF boundary
        v
FastAPI gateway + static client
        |
        | identity and application authorization boundary
        +---- Identity / matter membership / ethical walls
        +---- Legal workflow services (HITL, drafting, deadlines, post-resolution)
        +---- Evidence quarantine and parsing boundary
        +---- Citation/knowledge retrieval boundary
        +---- Audit and job execution boundary
        |
        | database/service credentials
        v
PostgreSQL ---- Redis ---- MinIO/object storage
        |
        | backup/operator/administrative boundary
        v
Backups, checkpoints, logs, monitoring

External/untrusted content boundary:
uploads, user prompts, retrieved law/cases, model output, attachments, model artifacts
```

### Boundary findings

| Boundary | Repository observation | Security consequence |
|---|---|---|
| Browser → API | `dependencies.py` accepts bearer headers; remediation backlog identifies frontend token storage | XSS can steal bearer credentials; cookie migration requires CSRF defense |
| Public → workspace | `/v1/platform/workspace/analyze`, specialists, and modes are intentionally unauthenticated | Input abuse, resource exhaustion, and accidental confidentiality exposure must be bounded |
| API → matter data | Several service methods enforce access, but multiple `main.py` routes only require authentication | IDOR/cross-matter access remains possible until every route has explicit object authorization |
| API → database | `connection.py` selects SQLite or psycopg; no transaction-local tenant context or RLS enforcement is shown | Application defect can become cross-tenant disclosure |
| Upload → parser/storage | `evidence.py` is identified as extension-oriented and filesystem-backed | Malicious/polyglot files can reach parsing or storage without full quarantine assurance |
| API → HITL/post-resolution | `state.py` uses process-local engines; `main.py` module header confirms process-local state | Restart loss, worker divergence, replay, and approval bypass risk |
| API → audit | Hash chain exists but chain-head append is not serialized | Concurrent events can fork or invalidate accountability |
| API → queue | `jobs.py` has a select-then-update claim pattern; Redis is declared but not authoritative | Duplicate execution and inconsistent recovery |
| API → legal sources | Citation verification is currently limited; official source integration is incomplete | False currency/pinpoint and unsafe court-ready claims |
| Compose → services | Development defaults and fixed example secrets are present in `docker-compose.yml` | Unsafe if copied to production; ports expose stateful services directly |

## 3. Assets and sensitivity

| Asset | Examples | Required protection |
|---|---|---|
| Client/matter content | names, facts, communications, evidence, decisions | Highest confidentiality; tenant/matter isolation; encryption; retention controls |
| Privileged material | solicitor-client communications and derivatives | Privilege classification, restricted access, export review, no content logging |
| Evidence originals | uploaded bytes, metadata, hashes, page/span provenance | Immutable originals, quarantine, malware scanning, versioning, chain of custody |
| Identity/session data | password hashes, session tokens, MFA state | Strong hashing, opaque tokens, rotation, revocation, rate limits, secure cookies |
| Ethical-wall/conflict state | memberships, parties, waivers, revocations | Deny-first enforcement; tamper-evident change history |
| Legal workflow state | consent, exceptions, reviews, approvals, JR clocks | Durable, versioned, idempotent, transactional, actor-attributed |
| Legal knowledge | statute versions, decisions, citation results | Authoritative sourcing, currency, hash, retrieval date, provenance |
| Audit ledger | security and legal action history | Serialized append-only writes, restricted role, external signed checkpoints |
| Model prompts/outputs | conversation text, attachments, generated drafts | Tenant isolation, minimization, provider policy, injection defenses, retention limits |
| Infrastructure secrets | DB, Redis, S3, signing and model-provider credentials | Secret manager, rotation, least privilege, never in logs/repository |

## 4. Actors and attacker profiles

- Unauthenticated internet user or automated scanner.
- Authenticated ordinary user attempting horizontal or vertical privilege escalation.
- Organization administrator attempting to bypass an ethical wall.
- Compromised browser through XSS, extension, shared device, or token theft.
- Malicious uploader targeting AV, PDF/OCR/parser, storage, or downstream model context.
- Prompt-injection content embedded in evidence, retrieved sources, or conversation attachments.
- Compromised/incorrect external model or legal-source provider.
- Worker racing another worker or replaying an operation.
- Malicious or careless operator/database administrator.
- Supply-chain attacker altering Python packages, container images, model artifacts, or JavaScript assets.

## 5. Threat register

Risk uses **Critical / High / Medium / Low** based on plausible impact and current exposure. “Current control” means evidenced in repository, not assumed deployment configuration.

| ID | Threat / abuse case | STRIDE | Affected components | Current control | Gap | Risk | Required mitigation / acceptance evidence |
|---|---|---|---|---|---|---|---|
| TM-01 | Steal bearer token from browser storage and impersonate user | S/I/D | frontend, identity, API | Token hashing/revocation exists | JavaScript-readable storage; no complete cookie/CSRF flow | Critical | P0-05; XSS/token scan, fixation, rotation, logout, CSRF tests |
| TM-02 | Credential stuffing or account enumeration | S/D | register/login | Password verification and generic auth errors partly present | No evidenced distributed rate limiting/MFA enforcement | High | Per-IP/account throttles, MFA policy, alerting, enumeration-safe responses |
| TM-03 | Access another matter by changing `matter_id` | E/I | `main.py` HITL/post-resolution; selected platform routes | `CurrentUser`; `require_matter_access` exists and is used on deadlines | Authentication is mistaken for object authorization on several routes | Critical | P0-04 and route-matrix closure; all inaccessible-object tests fail closed |
| TM-04 | Access object by guessed consent, exception, production, or conversation ID | E/I | resource-ID routes | Some services resolve ownership | No uniform route policy or proven object→matter authorization | Critical | Resolve resource under tenant context, then authorize; IDOR suite |
| TM-05 | Owner/admin bypasses ethical wall | E/I | identity/matter authorization | `can_access_matter()` checks ethical wall before role | Not database-enforced; incomplete route use | Critical | P0-03/P0-04; owner/admin ethical-wall tests across every matter operation |
| TM-06 | Cross-tenant query caused by missing application predicate | I/E | PostgreSQL and all tenant tables | Service checks and `org_id` fields exist in portions | No evidenced FORCE RLS/transaction tenant context | Critical | P0-03; FORCE RLS, least-privilege role, pool-reuse isolation tests |
| TM-07 | CSRF performs mutation after cookie migration | S/T | all POST/PUT/PATCH/DELETE | CORS allowlist outside development | CORS is not CSRF; no complete token validation | High | P0-05; origin plus synchronizer/double-submit token tests |
| TM-08 | XSS through generated/user legal text steals data or acts as user | S/I | frontend rendering, conversations, drafts | Input models; proposed CSP | Output escaping/sanitization and CSP not fully evidenced | High | Strict contextual escaping, no unsafe HTML, CSP, browser security tests |
| TM-09 | Public workspace receives live confidential information | I | unauthenticated analyze route, public demo | `enforce_public_text()` pattern scanning; public safety flags | Regex detects only a narrow identifier set; prompts may persist/log | High | Synthetic-only UX, content minimization, no persistence/model forwarding, DLP warning, rate limits |
| TM-10 | Malicious upload exploits parser/OCR/AV or masquerades by extension | T/D/E | evidence, PDF/OCR | Quarantine status fields and basic checks | No proven seven-state quarantine/content detection/real AV | Critical | P0-08; sandbox parsing, size/time/decompression limits, malicious corpus |
| TM-11 | Non-released or blocked evidence is processed or downloaded | I/E | evidence and object access | Quarantine field | Release-state authorization is not proven at every consumer | Critical | Central released-object capability check; deny tests across extraction, AI, export, signed URLs |
| TM-12 | Evidence original is overwritten, deleted, or loses provenance | T/R | filesystem/MinIO | SHA-256 and storage URI fields | Filesystem fallback; immutable/versioned object controls not production-enforced | Critical | P0-09; object lock/versioning/encryption, no overwrite, restore/hash proof |
| TM-13 | Embedded prompt injection causes model to disclose data or bypass policy | E/I | conversation, documents, RAG, future providers | Human-review/court-ready flags | No documented instruction/data separation or tool permission model | High | Treat retrieved text as data, scoped tools, output DLP, tenant-scoped retrieval, red-team suite |
| TM-14 | External model provider retains client data or trains on it | I | future multi-model providers | Private-inference model scope represented in consent | Provider enforcement, region, retention, and egress controls not implemented | Critical | Provider allowlist, data-classification router, no-training contracts, Canadian-region policy, explicit consent |
| TM-15 | Concurrent audit appends fork or corrupt chain | T/R | `backend/audit/ledger.py` | Hash chaining | Head read/insert not serialized | Critical | P0-06; 100 concurrent writer proof and transactional head |
| TM-16 | Runtime/DB admin alters or deletes audit history | T/R | audit DB | Application convention is append-only | DB grants/checkpoints do not prove immutability | High | P0-07; writer-only role, deny mutation tests, external signed checkpoints |
| TM-17 | Approval, consent, or exception state disappears after restart | T/R/D | `backend/api/state.py`, HITL | In-memory controls and audit calls | Process-local state and worker divergence | Critical | P0-10; durable state machine, optimistic version, idempotency, outbox, restart tests |
| TM-18 | Post-resolution/JR clock state disappears or crosses matters | T/D/I | post-resolution engine | Authenticated routes, some audit events | Process-local maps; routes lack explicit matter authorization | Critical | P0-11/P0-04; durable tenant-owned rows, locked clock processing |
| TM-19 | Two workers execute the same consequential job | T/R/D | jobs/Redis | Status fields/queue scaffold | Non-atomic claim and incomplete lease/DLQ | High | P0-12/P0-13; competing worker, crash/reclaim, idempotent effect tests |
| TM-20 | Redis outage silently falls back to unsafe local queue | R/D | jobs/readiness | Readiness endpoint exists | Redis is not proven authoritative and readiness does not check it | High | Production-required dependency, no silent fallback, truthful readiness/alerts |
| TM-21 | False or stale citation is marked verified/court-ready | T/R | citations/knowledge/drafting | Citation records, source metadata, `court_ready` default false | Keyword-level verification; currency/pinpoint/treatment incomplete | Critical | P0-14; official source, quote/pinpoint/currency fixtures, fail-closed status |
| TM-22 | Deadline result is treated as confirmed despite uncertainty | T/R | deadline engines/routes | API forces `human_confirmed=False`; audit events | Separate approval persistence and full legal calendar accuracy remain incomplete | High | Durable approval event, holiday/service rules, authoritative fixtures, visible provisional status |
| TM-23 | Caller self-attests export approvals to obtain court-ready manifest | E/T/R | `/exports/manifest` | Export service may apply blockers | Body accepts several approval booleans directly | Critical | Approvals must be separate actor-attributed persisted events; ignore self-attestation |
| TM-24 | Same actor reviews and approves or releases stale content | E/T/R | production routes | Same-person override fields and snapshot hashes exist conceptually | Role checks, durable separation, and stale-snapshot enforcement not proven | High | P0-10; reviewer/approver roles, two-person rule, signed snapshot comparison |
| TM-25 | Sensitive content leaks through logs, exceptions, SSE errors, health | I/R | API, audit, streaming | Exception schema discourages raw content; health summarizes issues | Broad exception text can reach clients; logs/redaction not centrally governed | High | Error envelopes, content-free telemetry, secret/PII redaction tests, restricted logs |
| TM-26 | Development CORS/default secrets/services reach production | S/I/E | main, compose, Postgres/Redis/MinIO | Wildcard CORS forbidden outside development | Compose has fixed dev credentials and exposed stateful ports | Critical if deployed | Production config validator, secret manager, network isolation, TLS/auth for dependencies |
| TM-27 | Backup is absent, corrupt, incomplete, or leaks client data | I/D | PostgreSQL, MinIO, audit | Persistent volumes in compose | No evidenced encrypted backup/restore drill | Critical | P0-16; encrypted immutable backups, access controls, restore/hash/audit verification |
| TM-28 | Dependency, container, or model artifact is malicious | T/E | pip, Docker, HF model | Version floors and model docs | Unpinned transitive dependencies/images; no signatures/SBOM/model hash policy | High | Lockfiles, digest-pinned images, SBOM/scanning, signed artifacts, model allowlist/hash |
| TM-29 | Registration creates unlimited organizations/owners | E/D | `/auth/register` | Public-demo persistence rejection | In non-demo mode route is unauthenticated without invite/admin provisioning | High | Deployment policy: invite/admin provisioning, rate limits, verified email, audit |
| TM-30 | Audit verification exposes global integrity metadata to any member | I | `/audit/verify` | Authentication required | No admin/auditor role; global scope may reveal operational information | Medium | Restrict role/scope, return tenant-safe result, audit verification access |
| TM-31 | Health/status discloses topology or exception strings | I | `/health`, `/health/ready`, platform status | Useful readiness checks | Raw dependency exceptions and module details may aid attackers | Medium | Public shallow probes; protected operator diagnostics; no credentials/DSNs/errors |
| TM-32 | Conversation attachments reference unauthorized objects | E/I | conversation send/stream | Conversation service authorization | Attachment dictionaries are caller-controlled; target authorization unclear | Critical | Typed attachment IDs, resolve under tenant/matter and released-state policies |
| TM-33 | SSE stream returns internal exception details or continues after revocation | I/E | stream route | Auth at stream start | Generator emits `str(e)`; no midstream auth/revocation/backpressure policy | High | Generic errors, cancellation/time limits, revocation checks for long operations |
| TM-34 | File path traversal through static icon route | I | `/icons/{name}` | `is_file()` check | Containment check is not explicit | Medium | Resolve and enforce path under icon root; traversal tests |

## 6. Critical attack paths

### AP-1 — Cross-matter legal-work disclosure

1. Attacker authenticates as a valid user.
2. Attacker learns or guesses another `matter_id` or resource ID.
3. Route accepts `CurrentUser` but does not call matter authorization.
4. Process-local/global service returns or mutates target state.
5. Missing RLS allows the application defect to reach stored data.

**Break path at:** route object authorization, service deny-first checks, FORCE RLS, tenant-safe object lookup, and audit alerts.  
**Release test:** every matrix row marked matter/resource-bound is tested with outsider, cross-org, revoked, ethical-wall, read-only, writer, and admin identities.

### AP-2 — Malicious evidence to model/tool execution

1. User uploads a disguised or malformed document.
2. Extension/content type is trusted or scanner fails open.
3. Parser/OCR processes hostile bytes.
4. Extracted prompt injection enters a model context.
5. Model invokes a future tool or leaks another source.

**Break path at:** byte-first quarantine, sandbox/limits, mandatory AV and type validation, released-only retrieval, instruction/data separation, scoped tool capability, and output DLP.

### AP-3 — Fraudulent court-ready export

1. Caller submits approval booleans or targets another production ID.
2. In-memory workflow lacks durable actor/state separation.
3. Citation/evidence/privilege status is stale or incomplete.
4. Release occurs without an atomic snapshot check.

**Break path at:** persisted approval events, object authorization, two-person rule, immutable content snapshot, full gate query in one transaction, and signed export manifest.

### AP-4 — Accountability failure under concurrency

1. Concurrent API/worker actions read the same audit predecessor or job state.
2. Audit chain forks and/or work executes twice.
3. Approval/export side effects become disputed.
4. Restart removes in-memory evidence of the sequence.

**Break path at:** serialized audit head, atomic job lease, idempotency keys, transactional outbox, durable workflow versions, and external checkpoints.

## 7. Required production control baseline

### Identity and session

- Opaque server-side sessions, secure cookies, CSRF, MFA for privileged roles, strong password hashing, rotation/revocation, login throttling, and session inventory.
- Separate authentication from organization, role, matter, ethical-wall, and resource-state authorization.

### Tenant and privilege isolation

- FORCE RLS with least-privilege runtime role and transaction-local immutable context.
- Every tenant-owned record carries `org_id`; every matter-owned object carries or safely derives `matter_id`.
- Ethical walls override owner/admin; privilege and export policies are separate from consent.

### AI and provider controls

- Model-provider registry with approved capabilities, region, retention/no-training status, supported data classifications, model/version, and health.
- Default deny for client data egress. Prompt and retrieved content are untrusted data.
- No autonomous external action; scoped tools require explicit approval and immutable action records.

### Evidence and legal-output controls

- Seven-state quarantine, sandboxed extraction, immutable originals, page/span provenance, and released-only consumption.
- Verified citations and provisional deadlines remain visibly non-court-ready until separate human approvals.
- Exports are snapshot-bound, signed, and blocked by any unresolved evidence, citation, privilege, consent, or exception state.

### Infrastructure and operations

- Private networks, TLS, secret manager, least-privilege service identities, digest-pinned images, dependency locks, SBOM, vulnerability scanning, encrypted backups, restore drills, security telemetry, and incident runbooks.

## 8. Security verification plan

| Test suite | Required scenarios | Exit condition |
|---|---|---|
| Route authorization | missing token, cross-org, cross-matter, revoked, ethical wall, access levels, guessed resource IDs | 100% protected rows covered; no unexplained gap |
| Session/browser | XSS-resistant storage, CSRF, rotation, fixation, logout/revocation, expiry, rate limits | All negative cases fail closed |
| RLS | every tenant table, direct SQL, pooled connection reuse, owner/admin wall | No cross-tenant row visible/mutable |
| Upload/parser | EICAR, MIME mismatch, malformed PDF, polyglot, archive bomb, scanner outage | No non-released processing; fail closed |
| Workflow | replay, stale version, same-person approval, restart, multi-worker | One valid transition and audit event |
| Audit/queue | 100 appenders, competing workers, worker crash, DLQ | Valid chain; no concurrent duplicate effects |
| Legal safety | wrong quote/pinpoint, stale law, source outage, false approval | `court_ready=false`; explicit blocker/audit |
| Recovery | database/object restore, hash reconciliation, audit checkpoint | Recovery objectives met with integrity proof |
| Supply chain | dependency/image/model scan and signature/hash validation | No unaccepted critical/high vulnerabilities |

## 9. Residual risk and release decision

Even after Gate 0, legal accuracy, privilege characterization, provider behavior, insider access, and novel prompt/parser attacks retain residual risk. Production use therefore requires ongoing human supervision, security monitoring, legal-content evaluation, privacy assessment, incident response, and periodic penetration/adversarial testing.

**Current decision:** the repository remains an Internal Alpha. Existing public-demo guards reduce some exposure but do not authorize live client data or public multi-tenant operation.

## 10. Traceability

| Threat group | Backlog controls |
|---|---|
| Identity/browser | P0-04, P0-05, P0-16, P0-17 |
| Tenant/ethical-wall isolation | P0-03, P0-04, P0-17 |
| Audit integrity | P0-06, P0-07, P0-16, P0-17 |
| Evidence quarantine/storage | P0-08, P0-09, P0-16, P0-17 |
| Workflow persistence | P0-10, P0-11, P0-17 |
| Queue concurrency | P0-12, P0-13, P0-16, P0-17 |
| Legal source/output integrity | P0-14, P0-17 |
| Model/supply chain | P0-15, P0-16, P0-17 |
| Database foundation | P0-01, P0-02, P0-03 |
