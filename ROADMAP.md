# Roadmap — BC Legal AI Associate

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
| 4 | Authentication + isolated matters | Not started |
| 5 | OCR + page-level document citations | Not started |
| 6 | Official-source legal retrieval | Partial (BC Laws discipline + local extracts) |
| 7 | Authority verification gate | Schema only |
| 8 | Structured legal workflows / agents | Scaffold |
| 9 | BC court templates + DOCX/PDF export | Templates partial; export engine not started |
| 10 | Comprehensive legal evaluations | Not started |
| 11 | Privacy and regulatory review | Not started |
| 12 | Innovation Sandbox if serving the public | Not started |

**Priority:** verified research engine + record-linked evidence engine.
