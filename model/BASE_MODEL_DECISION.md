# Base Model Decision — BC Legal AI

**Decision authority:** Designated foundational/base model selection for BC statutory + RTB + judicial review assistance  
**Date:** 2026-07-21  
**Status:** Binding design choice for this workbench (revisit only if hardware or license constraints force a change)

**Extended by:** [`FINE_TUNING_DESIGNATION.md`](FINE_TUNING_DESIGNATION.md) (same date) — ratifies **QLoRA / instruction tuning** as the selected adaptation method; **rejects full fine-tune** as primary. That document is binding for training methodology and data composition.

---

## 1. Decision (chosen base model)

| Role | Model | Hugging Face ID |
|------|--------|-----------------|
| **Primary base (recommended)** | **Qwen2.5-14B-Instruct** | `Qwen/Qwen2.5-14B-Instruct` |
| **Deployable default (Spaces / 24GB)** | **Qwen2.5-7B-Instruct** | `Qwen/Qwen2.5-7B-Instruct` |
| **Fallback (max compatibility)** | **Llama 3.1 8B Instruct** | `meta-llama/Llama-3.1-8B-Instruct` |

### Why this family

1. **Instruction quality** for multi-step legal workflows (IRAC, JR, evidence packaging).  
2. **Long context** (important for RTB decisions + statute extracts in one prompt).  
3. **HF ecosystem** maturity (LoRA, vLLM, transformers, Spaces patterns).  
4. **License** suitable for research and most product paths (confirm current license card before commercial ship).  
5. **Not** a legal-only encoder (Legal-BERT): we need generative counsel-assist behaviour.

### Why not pure “legal specialty” base alone

Specialty legal LMs are often outdated, narrow jurisdiction (US), or weak on BC procedure.  
**Currency of law cannot live only in weights** — legislation changes; the system must retrieve **today’s BC Laws** at inference.

---

## 2. Architecture (mandatory)

```
┌─────────────────────────────────────────────────────────────┐
│  USER (SRL / counsel assist)                                │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  ORCHESTRATION (skills: counsel, tenancy, legislation-admin)│
│  - Classify task, forum, stakes                             │
│  - Force source hierarchy                                   │
└───────────────────────────┬─────────────────────────────────┘
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
   ┌─────────────┐  ┌──────────────┐  ┌────────────────┐
   │ BC LAWS RAG │  │ RTB CanLII   │  │ JR CanLII RAG  │
   │ statutes    │  │ decisions    │  │ court reviews  │
   │ regs/rules  │  │ (secondary)  │  │ (secondary)    │
   │ CURRENT +   │  │              │  │                │
   │ HISTORICAL  │  │              │  │                │
   └──────┬──────┘  └──────┬───────┘  └────────┬───────┘
          └─────────────────┼──────────────────┘
                            ▼
              ┌──────────────────────────┐
              │ BASE MODEL (Qwen2.5-*)   │
              │ + optional LoRA adapter  │
              └──────────────────────────┘
```

| Data type | Allowed primary source | Forbidden as statute text |
|-----------|------------------------|---------------------------|
| BC statutes, regs, rules | **BC Laws only** | CanLII, blogs, firm sites, memory |
| RTB decisions | CanLII / official RTB publications | Invented decisions |
| Judicial review / appeal decisions | CanLII / official courts | Invented citations |
| Training pairs for style/procedure | Synthetic from **verified** sources only | Unverified scrape dumps |

**Principle:** Base model = **reasoner + drafter**.  
**BC Laws RAG = source of statutory truth.**  
Weights may learn *style and structure*; they must **not** be trusted as the current statute text.

---

## 3. Legislation currency requirement

Before any statutory claim in training data **or** inference:

1. Retrieve from **https://www.bclaws.gov.bc.ca/**  
2. Record **“current to”** line and **access date**  
3. For event-dated analysis, retrieve **historical / point-in-time** version when available  
4. Store both versions with metadata:

```json
{
  "enactment": "Residential Tenancy Act",
  "citation": "SBC 2002, c 78",
  "bclaws_url": "https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/02078_01",
  "currency_line": "This Act is current to July 14, 2026",
  "accessed_on": "2026-07-21",
  "version_kind": "current_consolidated",
  "event_date": null,
  "section_ids": ["5", "28", "29", "38"]
}
```

Never train or serve a statute chunk without that metadata.

Local verified sample: `legislation/court-ready/` (RTA + JRPA verification log).

---

## 4. Training data plan

### 4.1 Corpus A — BC Laws (primary)

| Item | Method |
|------|--------|
| Scope | RTA, MHPTA, JRPA, ATA (as applicable), Supreme Court Rules if published officially, key regulations |
| Ingest | Official HTML/PDF from BC Laws only |
| Chunking | Section/subsection boundaries; keep exceptions with parent section |
| Labels | current vs historical; access date; currency line |
| Refresh | Automated re-fetch + diff before any production deploy |

### 4.2 Corpus B — RTB decisions (CanLII)

| Item | Method |
|------|--------|
| Scope | Published RTB / dispute resolution decisions on CanLII |
| Use | Fact-pattern → issues → held → RTA sections **as cited** (then re-verify pins on BC Laws) |
| Caution | Decision may cite old numbering; **always re-map pins via BC Laws** before training labels |

### 4.3 Corpus C — Judicial review (CanLII)

| Item | Method |
|------|--------|
| Scope | BCSC / BCCA / SCC decisions reviewing RTB or admin tribunals (BC focus) |
| Use | Standard of review, procedural fairness, remedies, *Vavilov*-era framing |
| Caution | Do not treat reasons as substitute for current statute text |

### 4.4 Instruction format (LoRA / SFT)

Prefer **retrieval-augmented** training examples:

```
SYSTEM: You are a BC legal information assistant. Quote statutes only from provided BC Laws excerpts. Cite decisions only from provided CanLII excerpts. Never invent sections. Mark [UNVERIFIED] if missing.

USER: [task]
CONTEXT_BC_LAWS: [official excerpts + currency]
CONTEXT_RTB: [decision excerpts]
CONTEXT_JR: [case excerpts]

ASSISTANT: [answer using only context; structured FACT/LAW/ARGUMENT tags]
```

Fine-tune for:

- IRAC / counsel structure  
- Refusal to invent pins  
- Dual current/historical statute handling  
- SRL plain language vs counsel technical modes  

**Do not** fine-tune to “memorize the RTA” as sole source of truth.

---

## 5. Inference policy (runtime)

1. Classify query (statute / RTB practice / JR / procedure).  
2. If statute involved → **must** retrieve BC Laws (or fail closed with “not verified”).  
3. If RTB precedent → CanLII RTB retrieval.  
4. If JR → CanLII court retrieval.  
5. Call base model (+ LoRA) **with** retrieved context.  
6. Output tags: FACT / LAW / ARGUMENT / ASSUMPTION; confidence buckets.  
7. High-stakes → flag independent counsel.

---

## 6. Hardware / deployment mapping

| Target | Base | Notes |
|--------|------|--------|
| HF Space CPU demo | No full 14B; use **rule + RAG UI** or tiny model | Current `huggingface-space` / IntentKernel demos |
| HF ZeroGPU / 24GB | Qwen2.5-7B-Instruct + 4-bit / LoRA | Practical interactive assistant |
| Single 48GB GPU | Qwen2.5-14B-Instruct + RAG | Preferred quality |
| Multi-GPU / API | 14B+ or hosted endpoint | Production path |

---

## 7. Explicit non-choices

| Option | Why not primary |
|--------|-----------------|
| Legal-BERT only | Not generative |
| GPT-4/Claude as “base weights” | Not a local base; can be **orchestration** layer only |
| Training statutes from CanLII HTML | **Forbidden** for BC legislation text |
| Memorize-only fine-tune | Fails currency requirement |

---

## 8. Success criteria

- [ ] Zero statute quotes without BC Laws metadata in eval suite  
- [ ] Historical vs current statute tests pass  
- [ ] RTB decision citations resolve on CanLII or marked UNVERIFIED  
- [ ] Section-number regression test (e.g. quiet enjoyment = s. 28, not s. 22)  
- [ ] Human counsel review before any “file this” claim  

---

## 9. Disclaimer

This selection and pipeline design is **engineering / legal-information infrastructure**, not legal advice.  
Final authority for court materials: official BC Laws print/PDF + licensed counsel.

---

## 10. One-line designation

**I designate `Qwen/Qwen2.5-14B-Instruct` as the primary base model** (with `Qwen/Qwen2.5-7B-Instruct` as the default deployable base), **grounded at inference and in training labels by official BC Laws for all BC legislation**, and by **CanLII (or official courts) only for RTB decisions and judicial review jurisprudence**, under a **RAG-first, LoRA-second** architecture that enforces **current and historical currency checks**.
