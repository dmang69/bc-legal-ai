# BC Legal AI Associate

**Legal research, evidence analysis, and drafting support** for British Columbia civil and administrative work (superior court practice, RTB pathways, judicial review).

> **Not a lawyer. Not legal advice.**  
> This product is an **AI Legal Associate** — tools for research, record analysis, and drafting **support**.  
> It does **not** create a solicitor–client relationship and must not be held out as licensed to practise law in BC.  
> Court or client-facing use requires a **licensed supervising lawyer**, human verification, and approval.  
> Self-represented users: verify Rules, deadlines, service, and authorities before filing.  
> Complexity or risk → **`[INDEPENDENT COUNSEL RECOMMENDED]`**.

**Internal nickname only:** “AI Lawyer.” Do not use that label publicly.

| Status | Detail |
|--------|--------|
| Maturity | **Strong prototype / counsel workbench** — not a completed associate |
| Honest assessment | [`PRODUCT_STATUS.md`](PRODUCT_STATUS.md) |
| Build plan & V1 definition | [`ROADMAP.md`](ROADMAP.md) |
| Schemas / citation gate | [`architecture/`](architecture/) |
| Full ALA system architecture | [`architecture/ALA_SYSTEM.md`](architecture/ALA_SYSTEM.md) |
| Privilege / confidentiality layer | [`architecture/PRIVILEGE.md`](architecture/PRIVILEGE.md) |

```
AI Legal Associate
        ↓
Licensed supervising lawyer
        ↓
Human verification and approval
        ↓
Client or court document
```

---

## What is real today

| Component | Location |
|-----------|----------|
| Skill modules (tenancy, JR, counsel, BC Laws discipline) | [`skills/`](skills/) |
| Official RTA extracts + verification log | [`legislation/`](legislation/) |
| Living lexicon | [`lexicon/`](lexicon/) |
| Base model + RAG-first decision | [`model/`](model/) |
| Public Gradio **index** Space | [`huggingface-space/`](huggingface-space/) |
| Citation / approval **foundation** (schemas + tests) | [`architecture/`](architecture/), [`agents/`](agents/), [`tests/`](tests/) |

## What is not real yet (see PRODUCT_STATUS)

Auth, matter isolation, OCR, page-level citations, live research + treatment, deadline engine, court-form export, GraphRAG store, audit encryption, human finalize gates in a running app, production evaluation suite, cross-matter isolation in multi-user deploy.

**Without a verified research engine and a record-linked evidence engine, this remains a sophisticated skill/prompt interface.**

---

## Skills

| Skill | Path |
|-------|------|
| supreme-court-civil-counsel | [`skills/supreme-court-civil-counsel/`](skills/supreme-court-civil-counsel/) |
| bc-tenancy-procedure | [`skills/bc-tenancy-procedure/`](skills/bc-tenancy-procedure/) |
| bc-tenancy-advocacy | [`skills/bc-tenancy-advocacy/`](skills/bc-tenancy-advocacy/) |
| bc-judicial-review-guide | [`skills/bc-judicial-review-guide/`](skills/bc-judicial-review-guide/) |
| bc-tenancy-substantive | [`skills/bc-tenancy-substantive/`](skills/bc-tenancy-substantive/) |
| canlii-boa-builder | [`skills/canlii-boa-builder/`](skills/canlii-boa-builder/) |
| bc-legislation-admin | [`skills/bc-legislation-admin/`](skills/bc-legislation-admin/) |
| critical-reading | [`skills/critical-reading/`](skills/critical-reading/) |
| cognitive-awareness | [`skills/cognitive-awareness/`](skills/cognitive-awareness/) |
| + self-improvement, learning-mode, doc-coauthoring, legal-lexicon-cultivation | under [`skills/`](skills/) |

## Analytical tags (always)

**FACT · ALLEGATION · LEGAL ARGUMENT · INFERENCE · ASSUMPTION · PROCEDURAL HISTORY · RECOMMENDATION**

## Base model and fine-tuning

| Doc | Content |
|-----|---------|
| [`model/BASE_MODEL_DECISION.md`](model/BASE_MODEL_DECISION.md) | Qwen2.5 base + RAG-first |
| [`model/FINE_TUNING_DESIGNATION.md`](model/FINE_TUNING_DESIGNATION.md) | **QLoRA** selected; full FT rejected |

Primary: `Qwen/Qwen2.5-14B-Instruct`. Statute truth from **BC Laws**, not weights.

## Security

- Do **not** put unredacted client or litigation files on a **public** Hugging Face Space.  
- Production: private host, auth, matter ACL, encryption, audit, redaction before external model calls.  
- Secrets only in environment / HF Secrets — never in git.

## Quick start

```powershell
cd C:\Users\Dizzle\projects\bc-legal-ai
python tests\test_schemas_and_gates.py
```

1. Read `PRODUCT_STATUS.md` and `ROADMAP.md`.  
2. Load skills via your agent runtime as needed.  
3. Verify legislation on BC Laws before filing.  
4. Never finalize court drafts with `UNVERIFIED` authorities (`architecture.schemas.AuthorityStatus`).

## Repository

- GitHub: https://github.com/dmang69/bc-legal-ai  
- Default branch: `main`  
