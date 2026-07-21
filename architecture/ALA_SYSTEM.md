# ALA — AI Legal Associate: Full System Architecture

**Public designation:** BC Legal AI Associate (ALA)  
**Internal nickname only:** “AI Lawyer” — never use on public surfaces  
**Scope:** Multi-module legal reasoning and case management for **paralegal-level support** in landlord–tenant, small claims, and tribunal disputes (BC-first)

---

## 1. System overview

### Core principle

The system does **not** replace a lawyer.  
It replaces the ~40 hours of **drudge work** a paralegal does **before** a lawyer looks at the file.

```
Raw evidence dump
      →  Ingest / OCR / normalize
      →  Evidence matrix (conflicts, corroboration, gaps)
      →  Chronology + structured arguments
      →  Human / lawyer review
      →  Drafts & hearing binder (user files; system does not file)
```

### Supervised practice path

```
ALA (paralegal-level support)
        ↓
Licensed supervising lawyer
        ↓
Human verification and approval
        ↓
Client or court / tribunal document
```

### Explicit non-goals

| Does **not** | Instead |
|--------------|---------|
| Give legal advice with certainty | Options, risks, probabilities |
| Replace counsel at a hearing | Hearing **preparation** only |
| File with tribunal/court automatically | Prepares packages; **user** files |
| Guarantee outcomes | Risk assessment from evidence + precedents |
| Ship outputs without human review | Every submission path requires approval |

---

## 2. Architecture layers

### Layer 1 — Ingestion & normalization

```
┌─────────────────────────────────────────┐
│         RAW INTAKE (Multi-format)       │
│  PDF / JPG / PNG / DOCX / TXT / EML     │
│  / Voice memos / Video frame extracts   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│          CLASSIFIER (Zero-shot)         │
│  Routes each doc to a processing track: │
│  • Contract/Lease                        │
│  • Government Form/Notice                │
│  • Photograph (evidence)                 │
│  • Email/Correspondence                  │
│  • Financial Record                      │
│  • Legal Decision/Order                  │
│  • Miscellaneous                         │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         OCR ENGINE                       │
│  Tesseract + PaddleOCR (handwriting)     │
│  + optional legal fine-tune layer        │
│  • Skewed phone photos                   │
│  • Low-light enhancement first           │
│  • Multi-language (EN/FR for Canadian)   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      STRUCTURED EXTRACTION (NER +        │
│         Key-Value Parser)               │
│  dates, amounts, parties, addresses,    │
│  file numbers, statutes cited,          │
│  deadlines, obligations                 │
└─────────────────────────────────────────┘
```

**Output per document:** JSON with normalized fields + raw text + thumbnail + confidence score.  
**Hard rule:** preserve original bytes; derived text is a **separate** layer. Never silently modify source evidence.

**No hard character caps** on records: page/chunk index into storage; models receive retrieved slices, not a single truncated dump.

### Layer 2 — Evidence matrix

Navigates messy real-world dumps (mold photos, RTB decisions, city fines, leases, RCMP letters, eviction notices).

| Field | Type | Description |
|-------|------|-------------|
| evidence_id | UUID | Internal ID |
| source_file | string | Original filename |
| date_captured | datetime | When photo/doc was created (EXIF / metadata when available) |
| date_received | datetime | When it entered the system |
| evidence_type | enum | photo, contract, notice, correspondence, official_order, financial, other |
| parties_referenced | string[] | Names/entities mentioned |
| location_referenced | string | Property address if relevant |
| claim_tags | string[] | Legal claims supported (e.g. mold_hazard, non_repair, retaliatory_eviction) |
| contradicts | UUID[] | Conflicting evidence IDs |
| corroborates | UUID[] | Reinforcing evidence IDs |
| hearing_relevance | float | 0.0–1.0 relevance score |
| chain_of_custody | string | How obtained |
| ocr_confidence | float | Text extraction quality |
| human_notes | string | User annotations |
| admissibility_flag | enum | likely_admissible, questionable, inadmissible, needs_verification |

**Cross-reference engine auto-detects:**

- Temporal conflicts (claim “fixed by November” vs EXIF December)  
- Contradictory testimony / statements vs documents  
- Corroboration chains (photos + email + city inspection)  
- Gaps (claim with zero supporting evidence)

Schema implementation: `architecture/schemas.py` → `EvidenceItem`.

### Layer 3 — Legal knowledge base

```
legal_knowledge/
├── statutes/           # BC Laws-sourced; currency metadata required
│   ├── residential_tenancy_act_bc/
│   ├── judicial_review_procedure_act/
│   └── municipal_bylaws/   # e.g. kamloops/ — verify before reliance
├── case_law/
│   ├── rtb_decisions/
│   └── appeal_and_superior/
├── tribunal_procedures/
│   ├── rtb_hearing_process.md
│   ├── evidence_submission_rules.md
│   └── proof_of_service_requirements.md
├── policy_guidelines/  # RTB policy guidelines (gov sources)
└── citation_graph/
    └── relationships.db
```

**Retrieval:** hybrid vector (Qdrant/Weaviate) + SQL exact statute section + BM25; merge with reciprocal rank fusion.

**Statute rule:** BC statutory text only from **BC Laws** (not CanLII).  
**Case law:** CanLII + official courts; each hit stores authority metadata + treatment fields (`AuthorityRecord`).

**Case-law pipeline (target):**

1. Ingest new RTB/court decisions (scheduled)  
2. Extract holdings, facts, outcomes  
3. Index by issue tags  
4. Citation graph (cites / cited-by)

**Citation gate:** no case may be used in court-ready drafts unless verifier confirms existence, court/year, pinpoint, proposition fidelity, treatment, weight. Statuses: `VERIFIED` | `PARTIALLY_VERIFIED` | `UNVERIFIED` | `REJECTED`.

### Layer 4 — Reasoning & argument engine

Structured legal syllogism — **not** open-ended hallucination.

```python
class LegalArgument:
    claim: str
    legal_basis: list[StatuteRef]       # e.g. RTA s.32 — verify on BC Laws before filing
    factual_predicate: list[EvidenceRef]
    burden_of_proof: str                # typically balance of probabilities
    opposing_arguments: list[Counterargument]
    remedies_sought: list[Remedy]
    confidence: float
    evidence_gaps: list[str]
```

**Reasoning chain (example: mold / habitability):**

1. Rule identification (statute/reg/bylaw — official text only)  
2. Standard (health/safety/housing norms as applicable)  
3. Fact mapping → evidence IDs  
4. Causation / notice / failure to repair  
5. Damages / remedies framing  
6. Defense anticipation  
7. Rebuttal prep with evidence IDs  

**Precedent matching:** similar RTB outcomes → what won / what killed the claim → per-argument risk note.

**Grounding rule:** every factual claim → evidence_id **or** verified statute/authority. Else `INSUFFICIENT_EVIDENCE`.

### Layer 5 — Hearing preparation

| Module | Output |
|--------|--------|
| Chronology builder | Source-linked timeline from all evidence |
| Evidence / witness list | Numbered binder entries, relevance, tab refs, anticipated objections |
| Service tracker | Flags items lacking proof of service within required windows |
| Cross-exam bank | Questions grounded in matrix contradictions |

Example chronology shape:

```
2016-… — Lease signed (source: lease_from_2016.jpg)
2023-… — Mold first documented (source: 2023_back_unit.jpeg)
…
```

### Layer 6 — Client interaction

**RAG-grounded chat** (matter-scoped only):

- “What are my strongest arguments?”  
- “Has the landlord’s deadline to fix passed?”  
- “What evidence do I still need?”  
- “What did the 2023 RTB decision order?”  
- “Can the landlord legally evict me right now?”  

Answers must cite evidence IDs and statute sections. If ungrounded → refuse to invent.

**Draft generator** (human-reviewed before use):

- Tribunal submissions  
- Demand letters  
- Responses to notices  
- Cross-examination outlines  

Format/register appropriate to RTB / court; never auto-file.

---

## 3. Tech stack (target)

| Component | Technology |
|-----------|------------|
| Core LLM | Claude or GPT-4-class API **and/or** local Qwen2.5 (see `model/`) |
| Embeddings | bge-large-en-v1.5 or text-embedding-3-large |
| Vector store | Qdrant (self-hosted preferred for client data) |
| Relational DB | PostgreSQL (matters, evidence matrix, audit) |
| OCR | Tesseract + PaddleOCR; OpenCV preprocess |
| Documents | pdfplumber, PyMuPDF, python-docx |
| Backend | Python / FastAPI |
| Frontend | React + TypeScript (private); Gradio only for demos |
| Task queue | Celery + Redis |
| Keyword search | Elasticsearch or OpenSearch (optional) |
| Object storage | S3-compatible (HF Storage Buckets / MinIO) — **not** public Spaces for unredacted files |

---

## 4. End-to-end pipeline

```
User uploads N evidence files (matter-scoped)
        │
        ▼
┌─ Batch Ingestion ─────────────────────────┐
│  classify → OCR → extract → store raw +   │
│  structured (async job per file)          │
└──────────────┬───────────────────────────┘
               │
               ▼
┌─ Evidence Matrix Construction ────────────┐
│  claim tags, conflicts, corroboration,    │
│  gaps, admissibility flags                │
└──────────────┬───────────────────────────┘
               │
               ▼
┌─ Chronology + Argument Suggestion ────────┐
│  timeline, strongest claims, precedents   │
└──────────────┬───────────────────────────┘
               │
               ▼
┌─ User / Counsel Review ───────────────────┐
│  accept/reject, annotate, approve gates   │
└──────────────┬───────────────────────────┘
               │
               ▼
┌─ Output Generation ───────────────────────┐
│  binder, drafts, evidence index,          │
│  verification report (citation + evidence)│
└───────────────────────────────────────────┘
```

---

## 5. Critical design decisions

### Hallucination prevention

- Factual claims must trace to **evidence_id** or **verified** authority.  
- Reasoning constrained to syllogistic chains from available inputs.  
- Court-ready mode blocks `UNVERIFIED` / `REJECTED` authorities.

### Confidence (two tracks)

1. **OCR confidence** — extraction quality (blurry lease photo)  
2. **Argument confidence** — strength given evidence + precedent outcomes  

Both surface transparently; low OCR → force human review of that item.

### Canadian / BC jurisdiction focus

- *Residential Tenancy Act* (BC Laws)  
- RTB procedures and policy guidelines  
- Municipal bylaws as engaged (e.g. Kamloops) — always verify currency  
- Provincial health/housing standards as engaged  
- CanLII RTB / small claims / superior court / SCC as engaged  

Other provinces: swap statute layer + re-index case law.

### Messy real-world evidence

- EXIF when present  
- Filename timestamp patterns (e.g. `20251128_084839.jpg`)  
- Flag low-confidence extractions  
- Never assume text not clearly present  

### Security & privilege

- Matter-level isolation; no cross-matter ambient access  
- Private deploy for real files (not public HF Space)  
- Redact before external model transmission where required  
- Audit log every gate and export  
- **Solicitor–client privilege layer:** client-owned privilege, production gate, AI task scope — see [`PRIVILEGE.md`](PRIVILEGE.md)

---

## 6. Mapping to this repository

| Architecture piece | Repo path / status |
|--------------------|--------------------|
| Identity & non-goals | `PRODUCT_STATUS.md`, this doc |
| V1 definition & build order | `ROADMAP.md` |
| Proposition provenance | `architecture/schemas.py` → `Proposition` |
| Evidence matrix schema | `architecture/schemas.py` → `EvidenceItem` |
| Legal argument schema | `architecture/schemas.py` → `LegalArgument` |
| Citation / supervisor gates | `agents/verifier.py`, `agents/supervisor_gate.py` |
| Skills (paralegal reasoning prompts) | `skills/` |
| Official statute extracts | `legislation/` (BC Laws) |
| GraphRAG nodes/edges | `architecture/graph_model.md` |
| Layer 1–6 runtime | **Not built** — next implementation slices |
| Full-stack React / FastAPI / Qdrant | **Not built** |

---

## 7. Implementation priority (aligned with ROADMAP)

1. Matter isolation + PostgreSQL/SQLite evidence matrix  
2. Ingest pipeline (classify → OCR → structured extract; no char caps)  
3. Cross-reference engine (contradicts / corroborates / gaps)  
4. Chronology + argument builder (grounded)  
5. Hybrid legal retrieval + citation gate  
6. Hearing binder / DOCX export  
7. Private authenticated UI  
8. Evaluation suite (fabricated cites, leakage, OCR failures, …)

**Value hinge:** verified research engine + record-linked evidence matrix. Everything else is packaging.
