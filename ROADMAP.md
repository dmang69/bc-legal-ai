# Roadmap — BC Legal AI Associate

**Full system architecture (layers 1–6, stack, pipeline):** [`architecture/ALA_SYSTEM.md`](architecture/ALA_SYSTEM.md)

## Recommended production layout

```
bc-legal-ai/
├── frontend/                 # Gradio or web UI (private deploy for client data)
├── backend/
│   ├── api/
│   ├── auth/
│   ├── matters/
│   ├── documents/
│   ├── retrieval/
│   ├── citations/
│   ├── deadlines/
│   ├── drafting/
│   ├── exports/
│   └── audit/
├── agents/                   # Limited-responsibility stages (not autonomous filers)
├── architecture/             # Schemas, graph model, workflow stages
├── legal_knowledge/          # Statutes, rules, policy, authorities registry
├── templates/                # BCSC / RTB / correspondence
├── evaluations/              # Golden matters + adversarial tests
├── skills/                   # Agent skill packs (current foundation)
├── legislation/              # Official BC Laws extracts
├── tests/
├── Dockerfile
├── requirements.txt
└── README.md
```

Current repo already has strong content under `skills/`, `legislation/`, `lexicon/`, `templates/`, `model/`, and a public index Space under `huggingface-space/`. Backend/agents/evaluations are being scaffolded toward this layout.

---

## Associate workflow (controlled stages)

No single model call should run the full matter.

1. Intake  
2. Conflict and party-name check  
3. Jurisdiction analysis  
4. Limitation and deadline analysis  
5. Record ingestion  
6. Fact extraction  
7. Procedural chronology  
8. Issue identification  
9. Legal research  
10. Authority verification  
11. Application of law to facts  
12. Counterargument analysis  
13. Remedy analysis  
14. Drafting  
15. Citation audit  
16. Evidence audit  
17. Procedural-compliance audit  
18. Human approval  
19. Export  

### Specialized agents (limited responsibility)

| Agent | Role |
|-------|------|
| Intake Associate | Jurisdiction, document type, parties, deadlines, missing materials |
| Evidence Analyst | Facts, allegations, admissions, contradictions, timestamps, gaps |
| Research Counsel | Statutes, cases, Rules, policy |
| Citation Clerk | Citations, quotes, section numbers, pinpoints |
| Drafting Counsel | Petitions, responses, affidavits, submissions |
| Devil’s Advocate | Strongest adverse case |
| Procedural Clerk | Forms, filing, service, limits, exhibits, registry |
| Supervising Counsel Gate | Block finalize until warnings resolved or accepted |

Agents must **not** file, send, or exercise final legal judgment autonomously.

---

## Citation gate (mandatory)

| Status | Meaning |
|--------|---------|
| VERIFIED | Official/reliable source checked; pinpoint + proposition OK |
| PARTIALLY VERIFIED | Case/statute exists; proposition or pinpoint outstanding |
| UNVERIFIED | Generated or supplied; not checked |
| REJECTED | Does not exist or does not support the proposition |

**Court-ready mode** refuses to finalize any document containing **UNVERIFIED** (or REJECTED) authorities.

Research sources (authoritative layer):

- BC Laws — statutes and regulations only  
- Province of BC / RTB — forms, Rules of Procedure, policy guidelines  
- BC Courts — practice directions, forms, judgments, filing requirements  
- CanLII — decisions and citation relationships (not BC statute text for filing)  
- SCC decisions; federal legislation when engaged  

---

## Legal knowledge graph (GraphRAG)

**Nodes:** Person, Party, Lawyer, Case, Tribunal File, Court File, Document, Evidence Item, Fact, Allegation, Event, Issue, Statute, Section, Authority, Legal Test, Procedural Step, Deadline, Ground of Review, Remedy  

**Edges:** SUPPORTS, CONTRADICTS, CITED_BY, DECIDED_IN, SUBMITTED_AT, SERVED_ON, OCCURRED_BEFORE, APPLIES_TO, DISTINGUISHES, OVERRULES, AMENDS, EVIDENCE_FOR, EVIDENCE_AGAINST, REQUIRES_VERIFICATION  

---

## Security (client / litigation data)

A **public** Hugging Face Space is **unsuitable** for unredacted client or litigation files.

Production expectations:

- Private Space or private server  
- Authentication + RBAC + matter-level ACL  
- Encryption in transit and at rest  
- No raw-document logging; temp upload deletion  
- Redaction before external model transmission  
- Audit logs, session expiry, retention, incident response  
- Secrets only in HF Secrets / env — never in source  

---

## Human-review blocks

Require express approval before:

- Treating allegation as established fact  
- Adding authority to a court filing  
- Quoting a transcript  
- Finalizing a filing deadline  
- Making a concession / removing a ground  
- Waiving privilege  
- Signature-ready affidavit  
- Sending correspondence / filing with tribunal or court  

Every final product ships a **review report** (facts checked, unsupported statements, authorities verified, quotes, deadlines, cross-refs, human approval required).

---

## Evaluations (beyond three unit tests)

Benchmark matters must cover: fabricated-case resistance, wrong statutory section, deadline/service accuracy, fact/allegation separation, evidence citation accuracy, transcript timestamps, contradiction detection, adverse-authority recognition, standard of review, procedural fairness, prompt injection in evidence, cross-matter leakage, OCR failure modes, incorrect quotations, court-form compliance.

Target: hundreds of automated tests + a smaller set of manually graded legal files before calling anything “production.”

---

## Definition of completed Version 1

V1 is complete only when the system can reliably:

1. Open a separate **secure** matter  
2. Ingest a complete RTB or court record  
3. OCR and index every page  
4. Produce a source-linked chronology  
5. Distinguish facts, allegations, inferences, and arguments  
6. Identify jurisdiction, deadlines, and legal issues  
7. Research **current official** law  
8. Verify every authority and pinpoint  
9. Analyze both parties’ strongest positions  
10. Generate a court-formatted draft  
11. Produce separate evidence and citation audits  
12. Require human approval before finalization  
13. Export DOCX and searchable PDF  
14. Preserve a complete audit trail  

---

## Best next build order

| # | Step | Status |
|---|------|--------|
| 1 | Commit existing package to GitHub | Done (workbench); keep pushing |
| 2 | Default branch `main` | In progress |
| 3 | Deploy a **private** Hugging Face Space | Blocked on HF write token / privacy choice |
| 4 | Authentication + isolated matters | Partial: `MatterSession` + matter-partitioned matrix (no multi-user auth yet) |
| 5 | OCR + page-level document citations | Partial: Evidence Matrix full row schema + chronology (no OCR yet) |
| 5b | §7 structural eval suite | Partial: `evaluations/run_eval_suite.py` (no model inference) |
| 6 | Official-source legal retrieval | Partial (BC Laws discipline + local extracts) |
| 7 | Authority verification gate | Schema only |
| 8 | Structured legal workflows / agents | Scaffold |
| 9 | BC court templates + DOCX/PDF export | Templates partial; export engine not started |
| 10 | Comprehensive legal evaluations | Not started |
| 11 | Privacy and regulatory review | Not started |
| 12 | Innovation Sandbox if serving the public | Not started |

**Priority:** verified research engine + record-linked evidence engine.

---

## Phase 2–4 program (2026-07-21)

Aligned with CURRENT STATE design, public demo Space, RAG-first / LoRA-second, fail-closed legal safety.

### Phase 2 — Foundation

| Track | Goal | Deliverables (repo) | Status |
|-------|------|---------------------|--------|
| **2.1 Ingestion** | Confidence + HITL, classify, metadata, dedup, AV | `services/ingestion/`, `services/classifier/`, `services/transcription/`, `architecture/schemas/evidence_node_v1.json` | **Scaffold** (rule-based; no OCR/STT weights) |
| **2.2 Infrastructure** | Graph, PG, S3, vectors, queue, cache, gateway | `infra/docker-compose.yml`, `infra/k8s/`, `infra/secrets/`, `infra/logging/` | **Skeleton** (compose local; K8s not live) |
| **2.3 Compliance** | Privilege + BC Laws fail-closed + no-weights | `services/compliance/`, `middleware/privilege_guard.py` | **Scaffold** |

### Phase 3 — Legal reasoning engine (supervised)

| Track | Goal | Deliverables | Status |
|-------|------|--------------|--------|
| **3.1 Control plane** | Policy enforcement before reasoning/output | `hitl/control_plane/`, `approvals/`, `escalation/`, `schemas/` | **Implemented (in-memory)** |
| **3.1.A Consent** | Purpose categories, state machine, evaluate, withdrawal plan, ≠ waiver | `hitl/consent/` | **Implemented (in-memory)** |
| **3.1.B Exceptions** | Full taxonomy, NOTICE–CRITICAL, freeze, human resolve only | `hitl/exceptions/` | **Implemented (in-memory)** |
| **3.1.C Privilege** | Freeze snapshot, two independent pros, signed hash manifest | `hitl/privilege_check/production.py` | **Implemented (heuristic)** |
| **3.1.D Competency** | Licence, task fit, separate RTA/Rules/forms currency, conflict | `hitl/competency_gate/` | **Implemented (rules)** |
| **3.2 Knowledge base** | Source registry, treatment analyzer, snapshots, Form 66≠67 | `knowledgebase/*` | **Scaffold** |
| **Arch map** | Phase 3–4 implementation map + six design locks | `architecture/PHASE_3_4.md` | **Doc** |
| **Phase 3 API/DB contract** | consent, exceptions, approvals, knowledge-source | `architecture/contracts/` | **v0.1** |
| **Phase 3–4 FastAPI** | HITL + JR clock + 4-4 post-resolution routes | `backend/api/main.py` | **Started (in-memory)** |
| **JR clock** | 60-day + uncertainty + ATA s.57(2) path | `services/deadlines/jr_clock.py` | **Implemented** |

### Phase 4 — Clients + post-resolution

| Track | Goal | Deliverables | Status |
|-------|------|--------------|--------|
| **4.1 Portal** | MFA stub, dashboard, evidence, timeline, upload, a11y/i18n | `frontend/client/`, `services/client_portal/` | **UI scaffold + service stub** |
| **4.1 Messaging** | E2E placeholder, privilege flag, receipts | `services/messaging/` | **Stub** |
| **4.1 Consent center** | Client-facing consent UX API | `services/consent_center/` | **Implemented on ledger** |
| **4.2 Post-resolution** | Outcomes, enforcement, JR (Form 66 petition), retention | `post_resolution/`, `enforcement/`, `jr_pipeline/`, `retention/` | **Stub** |
| **4-4 Full Layer 6** | Outcome parse/clocks, compliance, escalation, enf/JR/stay, retention/destruction, LSBC scaffold | `services/post_resolution/*`, `services/compliance/lsbc_rules/` | **Implemented (in-memory heuristics)** |

---

## Critical path to production (authoritative order)

**Scorecard (2026-07-21):** ~40% designed · ~10–15% scaffold-implemented · **0% production-ready** for real client matters.

Do **not** start with HF Space “real associate,” LoRA, or Layer 4–6 polish. Wire foundations first.

| Wave | Build | Unblocks |
|------|--------|----------|
| **W0** | Secrets hygiene; never put client data on public Space | All later waves |
| **W1** | Postgres + `phase3_core.sql` + matter ACL + append-only audit | Consent, privilege, matters |
| **W2** | FastAPI gateway binding HITL contracts (consent/exceptions/approvals) | Any safe API |
| **W3** | Object store + **quarantine → classify → privilege → index** (Layer 1 core, no full OCR yet) | Evidence |
| **W4** | EvidenceNode persistence + graph edges + contradiction/timeline on real nodes (Layer 2) | Reasoning |
| **W5** | Privilege production gate on live exports + audit log (Layer 0 hard path) | Filings |
| **W6** | BC Laws retrieval + citation verify + PIT snapshots (knowledge) | Court-ready claims |
| **W7** | Deadline engine + JR clock human-confirm flags | Client deadlines |
| **W8** | Private client portal MFA + messaging Model B + consent centre | Real users |
| **W9** | Layer 4 hearing packs (DOCX) under lawyer approval | Hearing use |
| **W10** | Layer 6 decision ingest + compliance + Form 66 JR packs | After-hearing |
| **W11** | Eval suite (citation/privilege/leak/deadline) + pen-test + PIA | Pilot |
| **W12** | QLoRA only after RAG+evals green; private inference | Optional assist |

**Out of critical path until W6+:** full handwriting OCR, IMAP connectors, Neo4j at scale, garnishment automation, multilingual WCAG complete, public Space “full product.”

#### Phase 4-4 package map

| Subsystem | Path |
|-----------|------|
| Obligation parser | `services/post_resolution/obligation_parser/` |
| Outcome tracker | `services/post_resolution/outcome_tracker/` |
| Compliance monitor | `services/post_resolution/compliance_monitor/` |
| Escalation router | `services/post_resolution/escalation_router/` |
| Enforcement packs | `services/post_resolution/enforcement/` |
| JR pipeline | `services/post_resolution/jr_pipeline/` |
| Stay generator | `services/post_resolution/stay_generator/` |
| Retention schedule | `services/post_resolution/retention/` |
| Secure destruction | `services/post_resolution/destruction/` |
| LSBC rules scaffold | `services/compliance/lsbc_rules/` |

### One-page view

```
Phase 3  Make legally safe    →  HITL (A–D) + knowledge base + citation verifier
Phase 4  Make usable          →  portal + messaging + consent center + post-resolution
```

**Honest constraint:** in-memory ledgers and heuristics are not production multi-tenant security. Court-ready work still requires supervising lawyer + human approval + BC Laws re-verification. Live STT/OCR/CanLII treatment and real E2E crypto are not wired.
