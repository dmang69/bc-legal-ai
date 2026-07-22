# BC Legal AI Associate — Phase 4 Master Engineering Program

**Status:** Controlling engineering roadmap (corrected assessment applied 2026-07-22)  
**Repository:** `dmang69/bc-legal-ai`  
**Public name:** BC Legal AI Associate — research, evidence, and drafting **support** (not a lawyer)

> **Controlling build rule:** No feature may bypass an unfinished dependency merely because a demonstration can be made to work.

---

## 0. Reality check (repository state)

This plan matches the **actual** repository: a working legal-technology **prototype** with EvidenceNode logic, matter sessions, contradiction analysis, grounding gates, privilege scaffolding, legal-test models, and a rule-based Gradio demonstration — **without** production authentication, OCR, verified live research, persistent multi-user storage, or court-ready document export.

Architecture layers are largely **anticipated** in code/docs; full runtime, FastAPI multi-tenant platform, OCR, hybrid legal retrieval, and production storage are **not yet built**.

| Honest maturity | Level |
|-----------------|------:|
| Current repository | ~**25%** (Prototype) |
| Priority Zero (M0) completed | ~**28–30%** |
| Secure foundation + ingestion (M1–M2) | ~**45–50%** |
| Knowledge + retrieval + citations (M3) | ~**60–65%** |
| Reasoning, HITL, document generation (M4–M5) | ~**75–80%** (Supervised Beta target) |
| Client + post-resolution (M6–M7) | ~**85–90%** |
| Security/legal evaluation + pilot (M8) | **Production Candidate** |
| Ongoing operations | **Continuous Compliance** |

A legal platform is **never** literally “100% complete.” Law, forms, rules, threats, and models keep changing. Track **release levels**, not a permanent completion percentage.

### Release classifications

| Level | Meaning |
|-------|---------|
| **Prototype** | Local workbench and synthetic demonstration |
| **Internal Alpha** | Secure single-organization testing with synthetic data |
| **Supervised Beta** | Limited real matters under qualified human supervision |
| **Production Candidate** | Security, privacy, legal, and reliability gates passed |
| **Controlled Production** | Approved users and narrowly defined legal services |
| **Continuous Compliance** | Ongoing updates, monitoring, audits, retraining |

---

## 1. Corrections locked into this program

### 1.1 Scope is larger than “Big 18”

The **Big 18** accurately counts **core legal systems (Section B) only**. Full remaining program:

| Category | Major workstreams |
|----------|------------------:|
| Priority Zero remediation | 5 |
| Core legal systems | 18 |
| Infrastructure and security | 3 |
| Client portal (8+ modules) | 1 platform |
| Post-resolution (7+ modules) | 1 platform |
| Court / Windows integration | 1 program |
| Governance, testing, privacy, release | 4–6 |
| **Practical total** | **~33–36** |

**Task estimate (decomposed):** ~**485–695** core engineering tasks, plus **~55–75** Section G platform/distribution tasks.

| Work category | Estimated tasks |
|---------------|----------------:|
| Priority Zero | 25–40 |
| Identity, matters, consent, audit | 60–80 |
| Ingestion and Evidence Matrix | 80–110 |
| Legal knowledge and citations | 70–100 |
| Reasoning, agents and HITL | 60–90 |
| Deadline, procedure and drafting | 55–75 |
| Client and Windows integration | 45–65 |
| Post-resolution | 30–45 |
| Security, testing and release | 60–90 |
| **Core total** | **485–695** |
| Section G platform & distribution (M6A–F) | **+55–75** |
| **Grand total (approx.)** | **540–770** |

### 1.2 Modular monolith first — not microservices

Do **not** start with many microservices. That increases deployment complexity, authorization risk, distributed logging issues, privilege-boundary failures, transaction inconsistencies, development time, and cost.

**V1 production architecture: modular monolith + isolated workers**

```text
FastAPI application (modular monolith)
├── identity
├── matter
├── consent
├── privilege
├── ingestion
├── evidence
├── knowledge
├── citation
├── deadline
├── drafting
├── export
└── audit

Background workers (queue consumers — same codebase or thin worker entrypoints)
├── OCR
├── transcription
├── knowledge updates
├── document rendering
└── evaluation jobs
```

Split a module into a separate service **only when**:

- independent scaling is required;
- a security boundary requires separation;
- processing must occur in an isolated environment;
- release schedules conflict;
- the service has a stable API contract.

Code under `services/` is organized as **domain modules**, not deployable microservices, until a split criterion is met. See `architecture/MODULAR_MONOLITH.md`.

### 1.3 Simplified V1 data stack

| Component | Use |
|-----------|-----|
| **PostgreSQL** | users, orgs, matters, evidence, authorities, consents, approvals, audit metadata, **relationship tables** |
| **pgvector** | matter retrieval and legal-source embeddings |
| **S3-compatible object storage** | originals, rendered pages, audio, exports |
| **Redis** | queues, short-lived cache, rate limiting |
| **Worker queue** | OCR, transcription, rendering, updates |

**Defer:**

- **Neo4j** — add only when evidence/authority graphs outgrow relational edges + recursive SQL. Until then use `evidence_relationships`, `authority_relationships`, `entity_relationships`, `event_relationships`.
- **Time-series DB** — audit via append-only PostgreSQL (monthly partitions), hash chaining, immutable replication, WORM export. Separate TSDB is optional later.

### 1.4 Fine-tuning remains late

Fine-tuning must **not** begin until:

- official-source ingestion;
- point-in-time law;
- matter retrieval;
- citation verification;
- grounding gates;
- legal golden-set evaluations;
- source-linked model output;
- prompt and tool orchestration.

Otherwise the model may learn wrong section numbers, stale law, unsupported tests, case-specific assumptions, bad citation habits, or confidential patterns.

**RAG-first is correct:** legal truth comes from official sources, not model weights.

### 1.5 Windows connector — narrow security boundary

**Not** “index the whole PC.” Model:

```text
User selects approved folder
    → local connector inventories metadata
    → privilege + consent gate
    → user confirms selected documents
    → encrypted upload or local processing
    → matter-scoped indexing only
```

**Required controls:** no silent whole-drive indexing; no other-client files; configurable allowed folders; local exclusion list; preview before import; duplicate detection; consent confirmation; privilege classification; source-path provenance; revocable access; local audit log; OS credential protection. High-confidentiality matters: OCR / classification / redaction **on device** before data leaves.

### 1.6 What must not be built yet

Defer until the essential platform works:

- full model fine-tuning;
- large-scale autonomous agents;
- separate microservice per module;
- Neo4j migration;
- time-series audit database;
- automated tribunal/court filing;
- whole-computer Windows indexing;
- outcome prediction marketed to clients;
- unsupervised legal advice;
- public real-client intake;
- automatic privilege waiver;
- automatic settlement acceptance.

---

## 2. Nine milestones (M0–M8)

| ID | Name | Principal outcome |
|----|------|-------------------|
| **M0** | Emergency Remediation | Confidentiality + legal-integrity + repo risks removed |
| **M1** | Secure Platform Foundation | Identity, isolation, consent, conflicts, audit, storage |
| **M2** | Ingestion & Evidence | Quarantine, OCR, provenance, Evidence Matrix, review |
| **M3** | Legal Knowledge & Retrieval | Official law, PIT, hybrid retrieval, citation verification |
| **M4** | Reasoning & HITL | LegalTests, private inference, agents, privilege, competency |
| **M5** | Procedure & Court Export | Deadlines, forms, books, DOCX/PDF, redaction |
| **M6** | Client Portal & Windows Connector | Portal, messaging, accessibility, approved-folder connector |
| **§G / M6A–F** | Platform & Distribution | Tauri 2 + React; Workbench / Client / Portal installers & stores |
| **M7** | Post-Resolution | Decisions, enforcement, JR clock, retention |
| **M8** | Hardening & Controlled Release | Eval, security, privacy, pilot, production candidate |

### Critical path

```text
M0 Emergency Remediation
        ↓
M1 Identity + Isolation + Consent + Audit
        ↓
M2 Ingestion + Evidence + Provenance
        ↓
M3 Official Law + Retrieval + Citations
        ↓
M4 Legal Tests + AI + HITL
        ↓
M5 Deadlines + Procedure + Court Export
        ↓
M6 Client Portal + Windows Connector
        ↓
M7 Post-Resolution
        ↓
M8 Security and Legal Release Gate
```

**Allowed parallelism** (no dependency bypass):

- M2 document processing **alongside** M3 public legal-source ingestion  
- M5 template design **alongside** M4 agent design  
- M6 interface prototypes **alongside** M5 backend services  

**Hard stops:**

- no real client material in M6 before M1 and M2 pass;
- no public client intake before matter isolation;
- no legal conclusion before verified authority;
- no fine-tuning before RAG evaluation;
- no court-ready output before procedural validation;
- no disclosure before privilege review;
- no definitive deadline before human confirmation;
- no real matter data in public Git or public Hugging Face Space;
- no production release before legal and security evaluation.

---

## 3. Milestone detail

### M0 — Emergency Remediation

**Purpose:** Remove legal, confidentiality, and repository risks before further expansion.

| Epic | Work |
|------|------|
| **M0.1** Public repo cleanup | Inventory; replace with synthetic; purge history; review Actions/releases/PRs/issues/HF; rotate secrets; re-clone instruction |
| **M0.2** Confidential-data prevention | Patterns + `scan_confidential.py` + pre-commit + CI |
| **M0.3** Incorrect legal tests | Disable s.56 retaliation mapping; invalidate outputs; section-topic validation; source snapshot before ACTIVE |
| **M0.4** Stale dates | Synthetic labels; `HUMAN_CONFIRMED` only for definitive deadlines |
| **M0.5** Repo normalization | Protected `main`; package metadata; lock; Docker; CI; tag |

**Exit gate:** no known live matter in public Git history; no hard-coded live deadlines; incorrect LegalTest disabled; public demo synthetic-only; main protected; install/tests reproducible.

**Working status:** `docs/M0_RELEASE_GATE.md` (code/scanners/tag shipped; history rewrite + branch protection remain human ops).

### M1 — Secure Platform Foundation

**Purpose:** Identity, authorization, persistence, consent, and audit **before** real evidence.

| Epic | Scope |
|------|--------|
| M1.1 Authentication | MFA, passwordless, recovery, sessions, devices, suspension, rate limits, OIDC/SSO, service credentials |
| M1.2 Org & matter model | orgs, clients, users, matters, assignments, roles, parties, counsel, witnesses |
| M1.3 Authorization | RBAC/ABAC, matter grants, document ACLs, ethical walls, expiry, revocation |
| M1.4 Conflict checking | exact/alias/fuzzy, former clients, opposing parties, addresses, corps, waivers |
| M1.5 Consent service | purpose, category, external model auth, withdrawal, derived-data, notice versions |
| M1.6 Audit ledger | append-only, actor, hash chain, access/approval/privilege/export events |
| M1.7 Storage | PostgreSQL, object store, pgvector, Redis, encrypted backups, migrations |

**Exit gate:** authenticated actor on every action; org/matter-scoped queries; cross-matter isolation tests; conflict check before activation; consent/basis recorded; audit immutability; backup restore success.

### M2 — Production Ingestion and Evidence

**Purpose:** Unstructured records → verified, source-linked evidence.

Epics: quarantine; native extraction; OCR; media; metadata/provenance; dedup/versions; Evidence Matrix persistence; human evidence review.

**Exit gate:** originals immutable; every proposition page/span-linked; low confidence → HITL; no single context-window truncation of the record; duplicates/versions preserved; matrix survives restart/concurrency.

### M3 — Official Legal Knowledge and Retrieval

**Purpose:** Current, historical, verifiable authority.

Epics: source registry; statute/reg ingestion (current + PIT); RTB knowledge; court knowledge; update monitor; hybrid retrieval; citation verification (pinpoint, treatment, binding weight).

**Exit gate:** current law from official sources; historical by effective date; jurisdiction + weight; pinpoints for central propositions; superseded blocked from court-ready; source changes alert matters/templates.

### M4 — Legal Reasoning and HITL Control Plane

**Purpose:** Connect evidence and law through controlled reasoning.

Epics: lawyer-approved LegalTest registry; structured IREAC-style reasoning; private pinned inference; agent orchestration; exception service; privilege approval; competency gate.

**Exit gate:** model cannot bypass evidence/citation gates; tests approved and versioned; critical exception freezes output; privileged output needs authenticated review; competency confirmed; both-party analysis produced.

### M5 — Deadlines, Procedure, Drafting, Export

**Purpose:** Structured work product with human responsibility retained.

Epics: deadline engine; procedural engine; drafting (Form 66/67/32/33/109, RTB, memos, outlines); court books; export (DOCX, searchable PDF, PDF/A, package ZIP); redaction.

**Exit gate:** deadlines deterministic and explainable; correct BC forms; facts record-supported; legal propositions verified; exports pass privilege + procedure; DOCX/PDF render correctly.

### M6 — Client Portal and Windows Connector

**Delivery (controlling):** **Section G** — `docs/SECTION_G_PLATFORM_AND_DISTRIBUTION.md`.

| Surface | Name | Stack |
|---------|------|--------|
| Shared UI | All modes | React · TypeScript · Vite (`apps/platform-ui`) |
| Desktop | **BC Legal AI Workbench** | Tauri 2 (`apps/desktop-mobile`) |
| Mobile | **BC Legal AI Client** | Tauri 2 Android/iOS |
| Web | **BC Legal AI Portal** | PWA from same UI |

**Epics:** M6A foundation · M6B Windows · M6C macOS · M6D Android · M6E iOS · M6F PWA (+ product portal modules below).

**Portal product:** MFA, dashboard, evidence, preview, guided upload, timeline, tasks, deadlines, messages, consent centre, decision/enforcement/JR viewers, notifications, accessibility, multilingual.

**Windows connector (Tauri native plugin, not whole-drive search):** approved folder only; inventory; preview; consent; privilege; duplicates; local redaction (high confidentiality); encrypted transfer; revocation; local audit.

**Exit gate:** Section G §19 platform standard **and** product gates: client sees only authorized material; uploads quarantine; messaging crypto accurately described; no silent whole-drive scan; consent effective; accessibility testing passes; store installers signed for pilot maturity level.

**Delivery order:** web portal → PWA → Windows EXE → macOS DMG → Android/iOS beta → stores → enterprise MSI.

### M7 — Post-Resolution and Enforcement

Epics: decision ingest; order extraction; outcomes; compliance; monetary/possession enforcement; JR trigger; 60-day calculation; stay workflow; retention; legal holds; secure destruction.

**Exit gate:** terms human-confirmed; compliance tracked; enforcement by order type; JR alternatives calculated; holds block destruction; destruction covers derivatives and indexes.

### M8 — Production Hardening and Controlled Release

Legal golden matters; citation hallucination tests; deadline benchmarks; privilege red team; cross-matter isolation; prompt injection; pen test; threat model; PIA; vendor/model review; DR; IR exercise; accessibility audit; supervising-user training; controlled pilot; production release review.

**Final gate:** zero known cross-matter leakage; no citation-gate bypass; no critical security findings; backup restore tested; golden set approved; privilege red-team passed; supervisors trained; client disclosures approved; pilot scope formally defined.

---

## 4. Hard product rules (non-negotiable)

1. No public client intake before matter isolation  
2. No legal conclusion before verified authority  
3. No model fine-tuning before RAG evaluation  
4. No court-ready output before procedural validation  
5. No disclosure before privilege review  
6. No definitive deadline before human confirmation  
7. No real matter data in public Git or public HF Space  
8. No production release before legal and security evaluation  
9. No feature ships by demo alone when a dependency is unfinished  

---

## 5. Program metrics

| Metric | Initial target |
|--------|---------------:|
| Cross-matter leakage | 0 |
| Unverified citations in court-ready output | 0 |
| Unsupported facts in finalized output | 0 |
| Privilege-gate bypasses | 0 |
| Deadline engine benchmark accuracy | 100% on approved fixtures |
| Page-level provenance coverage | 100% |
| Critical security findings at release | 0 |
| Legal golden-set pass rate | ≥95% overall; 100% on critical controls |
| Public repository confidential-data findings | 0 |
| Backup restore success | 100% in scheduled tests |
| Human approval coverage for external outputs | 100% |

---

## 6. Sprint P0-1 (first development sprint)

**Objective:** remove immediate public-repository and legal-test risks.

Issues: M0-001…003, 005–010, 013, 016–018, 021, 023 (see M0 gate).

**Definition of done:** tests pass; confidential scan passes; public demo synthetic-only; incorrect LegalTest cannot execute; no live deadline displayed; main protected; clean install documented; remediation release tagged.

---

## 7. Related artifacts

| Artifact | Role |
|----------|------|
| `docs/M0_RELEASE_GATE.md` | M0 checklist status |
| `docs/M0_001_inventory.md` | Confidential inventory |
| `docs/SECTION_G_PLATFORM_AND_DISTRIBUTION.md` | **Section G** — full platform & distribution architecture |
| `docs/PLATFORM_AND_INSTALLATION.md` | Short pointer to Section G |
| `docs/github/LABELS.md` | GitHub labels |
| `.github/ISSUE_TEMPLATE/engineering_task.md` | Issue template |
| `architecture/MODULAR_MONOLITH.md` | Architecture decision |
| `architecture/WINDOWS_CONNECTOR_BOUNDARY.md` | Connector security model |
| `apps/platform-ui/` | React/Vite shared UI |
| `apps/desktop-mobile/` | Tauri 2 shell (primary packaging) |
| `PHASE_4_ROADMAP.md` | Legacy Phase 4 notes — **subordinate** to this document |
| `PRODUCT_STATUS.md` | Honest product maturity |

---

## 8. Correct next artifact

After M0 passes fully (including human ops):

1. GitHub milestones for M0–M8 (+ Section G / M6A–F labels)  
2. Label set from `docs/github/LABELS.md`  
3. Issue pack starting **M1** (identity + PostgreSQL + audit)  
4. Parallel **M6A** shell (React/Vite + unsigned Windows Tauri) against synthetic backend only  

**No real client portal features until M0 is accepted and M1 isolation is designed.** Unsigned Workbench shells and portal scaffolds may proceed with synthetic data only.

---

*This document is the controlling Phase 4 engineering roadmap for the BC Legal AI Associate.*
