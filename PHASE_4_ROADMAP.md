# Phase 4 — Client Interaction & Post-Resolution Engine

> **Controlling roadmap:** [`docs/PHASE_4_MASTER_ENGINEERING_PROGRAM.md`](docs/PHASE_4_MASTER_ENGINEERING_PROGRAM.md)  
> This file is a **subordinate** design note for M6–M7 themes. Architecture defaults below were corrected 2026-07-22: **modular monolith**, PostgreSQL + pgvector (not Neo4j/TSDB at V1), RAG-first (fine-tune late), Windows **approved-folder** connector only.

**Objective:** Make the system usable by real clients and supervising lawyers through the entire matter lifecycle.

## 4.1 Client Interaction Layer

### A. Client Portal & Dashboard

- MFA login
- Matter status (current deadline, next action, evidence tracker)
- Visual timeline (client-friendly version of chronology)
- Evidence upload status
- Latest decision or order

### B. Secure Messaging

**Architecture decision:** Either true E2EE (limited AI processing) OR controlled legal-workspace encryption (AI-enabled). Do not falsely claim both.

- Privilege flagging
- Message classification prompts
- Read receipts
- Delivery confirmation

### C. Guided Document Upload

- Document type classification
- Photo metadata capture (EXIF, date, location)
- Preview and confirmation
- Status tracking (uploaded → quarantined → processed → indexed)

### D. Consent Management Center

- Current consent state (visible to client)
- Purpose and scope (plain language)
- Withdrawal controls
- Complete history

### E. Deadline & Task Communication

- Automated reminders
- Completion confirmations
- Deadline status (calculated vs. human-confirmed)

### F. Accessibility

- Multi-language support (English, French, Punjabi, Mandarin, Tagalog)
- Screen-reader compatibility
- Mobile-first design
- Plain-language legal summaries

**Output:** `/frontend/client/`, `/services/client_portal/`

## 4.2 Post-Resolution Layer

### A. Outcome Tracking

- Decision ingestion (PDF → structured obligations)
- Compliance clock generation
- Predicted vs. actual outcome comparison
- Compliance monitoring ledger

### B. Compliance Monitoring

- Automated reminders (deadlines for repair, payment, vacating)
- Non-compliance detection
- Evidence ingestion (photos, receipts, inspection reports)
- Escalation routing

### C. Enforcement & Appeal Pipeline

**Enforcement:**
- RTB enforcement application generator
- Provincial Court monetary order filing
- Garnishment package generation

**Appeal / Judicial Review:**
- Error extraction from decision
- 60-day clock tracking (per ATA s.57)
- Draft petition scaffolding (Form 66, not Form 67)
- Draft stay application scaffolding (Form 32)
- Evidence binder (JR format)

### D. Document Retention & LSBC Compliance

- Retention schedule engine (evidence, privileged materials, drafts)
- Cryptographic destruction workflow
- Client request mechanism (return / destroy)
- LSBC compliance (minimum retention, privilege handling)
- Matter closure protocol

**Output:** `/services/post_resolution/`, `/services/enforcement/`, `/services/jr_pipeline/`, `/services/retention/`

## 4.3 Infrastructure Requirements (V1 — corrected)

### Database Architecture

- **PostgreSQL**: clients, matters, users, permissions, evidence metadata, **relationship tables**, append-only audit (+ hash chain)
- **pgvector**: semantic search across evidence and law
- **S3-compatible object store**: originals, pages, audio, exports
- **Redis**: job queue, short cache, rate limits
- **Not V1-required:** Neo4j (defer until relational graph is insufficient); dedicated time-series DB (defer; use partitioned Postgres audit)

### Application Architecture

- **Modular monolith** (FastAPI domain modules) — see `architecture/MODULAR_MONOLITH.md`
- Background **workers** for OCR, transcription, knowledge updates, rendering, evaluation
- Split to microservices only when scale, security isolation, or release cadence requires it
- Cache/queue: Redis

### Security

- AES-256 encryption at rest
- TLS 1.3 in transit
- Client-matter-specific keys (compromise of one matter doesn't expose others)
- Authentication: MFA required
- Authorization: Row-level matter access

## 4.4 Compliance Boundary

Before serving real clients, operate under one of:

- Licensed lawyer or law firm supervision
- Authorized legal-service-provider framework
- **Law Society Innovation Sandbox authorization** (recommended)
- Self-represented personal-use model

**Public-facing safeguards:**

- Never state the AI is licensed
- Identify the human supervisor
- Identify service scope
- State whether professional liability insurance applies
- Distinguish legal information from approved legal advice
- Prevent automatic filing or settlement
- Prevent AI-only privilege determinations

## 4.5 Implementation Order

**Sprint 1:** MFA, matter isolation, document quarantine

**Sprint 2:** Client portal (dashboard, evidence tracker, tasks)

**Sprint 3:** Secure messaging, consent center, accessibility

**Sprint 4:** Decision ingestion, compliance monitoring

**Sprint 5:** Enforcement package builder, JR pipeline, 60-day clock

**Sprint 6:** Retention, legal holds, destruction

**Sprint 7:** Production readiness (testing, security review, pilot)

## 4.6 Acceptance Gate

Phase 4 is complete only when:

- ✅ Clients use MFA
- ✅ Matters are isolated (no cross-matter data leakage)
- ✅ Uploads enter quarantine before indexing
- ✅ Messaging encryption claims are technically accurate
- ✅ Consent controls are understandable and enforceable
- ✅ Deadlines distinguish calculated from human-confirmed
- ✅ Accessibility tests pass (WCAG, screen readers, multi-language)
- ✅ Decisions can be ingested and analyzed
- ✅ Enforcement routes vary by order type
- ✅ 60-day JR workflow is rules-driven
- ✅ Retention and legal holds are operational
- ✅ No real-client document enters a public Space
- ✅ Every external release has an approval manifest
