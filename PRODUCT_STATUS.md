# Product status — honest assessment

**Public name:** BC Legal AI Associate  
**Internal nickname only:** “AI Lawyer” (do **not** use publicly)  
**Public positioning:** legal research, evidence analysis, and drafting **support**  
**Not:** a licensed lawyer, legal advice service, or representation

**Assessment date:** 2026-07-21  
**Verdict:** strong **prototype / counsel workbench** — **not** a completed AI Legal Associate

---

## What exists today (local + GitHub)

| Layer | Status |
|-------|--------|
| Agent skill modules (tenancy, JR, counsel, BC Laws discipline) | Present |
| Official RTA extracts + verification log (BC Laws) | Present |
| Lexicon / doctrine cards | Present |
| Base-model decision (Qwen2.5 + RAG-first) | Present |
| Gradio index Space (`huggingface-space/`) | Present (navigation + official links) |
| Publish scripts (GitHub / HF) | Present |
| Matter-isolated client files | Local-only via `matters/` gitignore |
| Production auth / multi-tenant security | **Absent** |
| OCR, page-level citations, citation gate | **Absent** |
| Live statutory/case research + treatment | **Absent** |
| Deadline engine, court-form export | **Absent** |
| GraphRAG knowledge graph | **Absent** |
| Human approval gates + audit trail | **Absent** |
| Meaningful legal evaluation suite | **Absent** |

**GitHub note (2026-07-21):** `https://github.com/dmang69/bc-legal-ai` is **not** empty. Remote holds the skills/legislation workbench (tree ~140 objects on `master`/`main`). It is **not** yet a full associate product with matter storage, OCR, verification, or court export. If a third-party “project package” described Gradio inference + five skills + three tests + 60k/140k truncation, that refers to a **demo package**, not the completed V1 system.

---

## Immediate deficiencies (production associate)

The current build does **not** yet provide:

- User accounts or authentication  
- Separate confidential case workspaces with cross-matter isolation  
- Persistent matter storage (beyond local ignored folders)  
- OCR for scanned court records  
- Page-level or paragraph-level source citations  
- Live statutory and case-law research  
- Authority validation / case treatment checking  
- Rules-based deadline calculation by service method  
- Structured fact and evidence databases  
- Court-form generation  
- Court-ready DOCX / searchable PDF export  
- Document redaction  
- Encryption controls, audit logs  
- Version control for legal authorities  
- Human approval gates  
- A meaningful legal evaluation suite  
- Protection against one client seeing another client’s information  
- Fixed production model + cost / token / rate controls  

Record limits of ~60,000 characters per file / ~140,000 combined (where present in demo readers) are **insufficient** for a full Book of Petition, transcript, affidavit record, or tribunal file. Production ingestion must be **chunked, page-indexed, and unbounded by a single context window**.

---

## Legal identity (non-negotiable)

```
AI Legal Associate
        ↓
Licensed supervising lawyer  (when used in practice)
        ↓
Human verification and approval
        ↓
Client or court document
```

- Do **not** hold the product out as a licensed lawyer or as qualified to practise law in BC.  
- Activities that can constitute legal services for others (legal advice, preparing court documents for others, negotiation/representation) engage **unauthorized-practice** risk — public offering requires careful scoping and, where appropriate, Law Society pathways (including **Innovation Sandbox** for non-traditional / AI-enabled pilots).  
- For lawyer-supervised use: the BC Code requires **supervision of delegated work** and retention of professional judgment by the lawyer.

This repository provides **legal information and drafting support tools**, not a solicitor–client relationship.

---

## What makes it a real associate (not a prompt UI)

Two systems determine value:

1. **Verified legal research engine** — official sources, currency, pinpoint, treatment, VERIFIED/REJECTED gate.  
2. **Record-linked evidence engine** — page/timestamp provenance, FACT vs ALLEGATION, immutable originals + derived text layers.

Without those, this remains a sophisticated skill/prompt interface.

---

## Related documents

- [`ROADMAP.md`](ROADMAP.md) — build order and V1 definition of done  
- [`model/BASE_MODEL_DECISION.md`](model/BASE_MODEL_DECISION.md) — model / RAG posture  
- [`architecture/`](architecture/) — schemas for matters, propositions, citations  
