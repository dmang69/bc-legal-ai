# Phase 3 — Legal Reasoning Engine Completion

**Objective:** Transform system from "safe demo" → "supervised legal reasoning engine."

**Deliverables:**

- HITL pipeline completion (4 subsystems)
- Legal knowledge base (sources, statutes, cases, templates)
- Citation verification
- Point-in-time law support

## 3.1 HITL Pipeline Completion

### A. Client Consent Capture & Tracking

**Purpose:** Record and enforce what processing a client has authorized, independent of privilege.

**Build:**

- Consent ledger per matter
- Granular consent categories (medical, tenancy, financial, photos, audio)
- Withdrawal mechanism with immediate revocation
- Privilege Engine integration
- Audit log (immutable, timestamped)

**Key rule:** Consent to processing ≠ waiver. Withdrawal of processing consent ≠ deletion.

**Output:** `/services/reasoning/hitl/consent/`

### B. Error & Exception Logging

**Purpose:** Malpractice-safe reasoning log.

**Build:**

- Hallucination attempt detection
- Contradiction logging
- Extraction confidence failures
- Legal test UNSUPPORTED / CONFLICTED states
- Severity levels: INFO → WARNING → CRITICAL
- Auto-escalation to supervising lawyer for CRITICAL events

**Output:** `/services/reasoning/hitl/exceptions/`

### C. Privilege Preservation Confirmation

**Purpose:** Prevent accidental waiver or inadvertent disclosure.

**Build:**

- Pre-output privileged-material scan
- Two-factor confirmation (review + approve, by different people)
- Waiver-risk detection (privileged doc inside evidence bundle)
- Logged review workflow
- Hard blocks on release without approval

**Output:** `/services/reasoning/hitl/privilege_check/`

### D. Competency Gate for Reviewing Lawyers

**Purpose:** Ensure the right lawyer signs off (not just "a lawyer").

**Build:**

- Practice area matching (RTB/tenancy ≠ corporate law)
- Jurisdiction currency (BC-licensed, RTA amendments current)
- Conflict check (no disqualifying relationships)
- Override protocol (backup reviewer identified)

**Output:** `/services/reasoning/hitl/competency_gate/`

## 3.2 Legal Knowledge Base

### A. Primary Source Database

- **Statutes:** BC Laws (RTA, regulations, historical versions)
- **Case law:** RTB decisions, BCSC/BCCA judicial review decisions
- **Tribunal rules:** RTB Rules of Procedure, BC Supreme Court Rules
- **Version control:** Point-in-time law retrieval (event date vs. current date)

### B. Update Mechanism

- BC Laws monitor (daily automated check)
- CanLII monitor (new relevant decisions)
- Change log with effective dates
- Version locking (analysis preserves law as of event date)
- Affected-matter identification and notification

### C. Template Library

- **Corrected forms:** Form 66 (petition), Form 67 (response), Form 32 (notice of application), Form 33 (application response)
- RTB dispute applications
- Stay applications
- Affidavit templates (Form 109)
- Evidence binder templates
- Chronology templates

### D. Citation Verification Pipeline

- Parse citation → verify existence → verify pinpoint → verify proposition
- Shepardizing equivalent (treatment analysis)
- Jurisdiction flagging (Ontario = persuasive, not binding)
- FULLY_VERIFIED status before court-ready output

**Output:** `/knowledgebase/`, `/knowledgebase/templates/`, `/knowledgebase/citation_verifier/`

## 3.3 Implementation Order

**Sprint 1:** Consent ledger, exception service, escalation

**Sprint 2:** Privilege-safe output gate, frozen snapshots, signed manifests

**Sprint 3:** BC Laws ingestion, case law indexing, citation verifier

**Sprint 4:** Template versioning, point-in-time statute retrieval

## 3.4 Acceptance Gate

Phase 3 is complete only when:

- ✅ Every reasoning operation checks consent or another processing basis
- ✅ Consent withdrawal blocks future optional processing
- ✅ Privilege is independent from consent
- ✅ Critical exceptions freeze affected workflows
- ✅ Every filing citation passes verification
- ✅ Point-in-time law is supported
- ✅ Templates are versioned
- ✅ Reviewer competence and conflicts are checked
- ✅ No output bypasses the privilege gate
