# Fine-Tuning Designation — BC Legal AI

**Decision authority:** Designated by the principal (2026-07-21) to select base model, training data composition, and fine-tuning methodology for the BC AI legal specialist (tribunals / RTB / judicial review).  
**Date:** 2026-07-21 (PDT)  
**Status:** Extends and ratifies [`BASE_MODEL_DECISION.md`](BASE_MODEL_DECISION.md) (same date). Binding for the workbench; revisit only on hardware, licence, or eval-driven grounds.  
**Character of this document:** Engineering and legal-information infrastructure design — **not legal advice**.

---

## 1. The three questions put to the model, and the answers

| Question | Designation |
|---|---|
| Full fine-tune? | **Rejected** as primary method. |
| LoRA? | **Selected.** QLoRA adapters, instruction-tuned. |
| Instruction tuning on legal Q&A pairs? | **Selected** as the dataset format for the LoRA SFT run — in retrieval-augmented form. |

**One-line designation:** *LoRA instruction tuning on retrieval-augmented legal Q&A pairs, on a Qwen2.5-Instruct base, with BC Laws as the sole statutory source of truth at both training-label time and inference time.*

---

## 2. Why not full fine-tuning

1. **Currency failure.** Legislation mutates. A full fine-tune bakes today's RTA into the weights and begins decaying the day training ends. Your own framework imposes a *legislation currency requirement* sourced exclusively from BC Laws; a memorize-first full FT is structurally incapable of honouring it without constant retraining.
2. **Catastrophic forgetting.** Full FT on a narrow BC tenancy/JR corpus degrades the general instruction-following and reasoning the counsel workflows depend on.
3. **Cost asymmetry.** Full FT of a 14B model requires multi-GPU infrastructure and repeated runs each time the corpus is corrected. QLoRA trains on a single 24–48 GB card, and the adapter (not the base) is what you version, swap, and roll back.
4. **Auditability.** A LoRA adapter is a small, diff-able artifact. When a section-number regression appears (the s. 22 vs s. 28 quiet-enjoyment failure mode is documented in this repo), you retrain an adapter in hours — not a base in days.

## 3. Why LoRA instruction tuning is the correct selected method

The adapter's job is **behaviour, not truth**:

- Enforce the analytical-tag discipline (FACT / ALLEGATION / LEGAL ARGUMENT / INFERENCE / ASSUMPTION / PROCEDURAL HISTORY / RECOMMENDATION).
- Refuse to invent pinpoints; emit `[UNVERIFIED]` when context is absent.
- Handle dual current/historical statute framing ("as at the event date" vs "current consolidation").
- IRAC structure, counsel-register vs SRL plain-language register switching.
- Fail-closed behaviour: when no BC Laws excerpt is in context, say so rather than recite.

Statutory truth is **retrieved**, never recalled. This is the RAG-first / LoRA-second architecture already ratified in [`BASE_MODEL_DECISION.md`](BASE_MODEL_DECISION.md).

## 4. Base model (ratified, with one flagged review item)

| Role | Model | HF ID |
|---|---|---|
| Primary base | Qwen2.5-14B-Instruct | `Qwen/Qwen2.5-14B-Instruct` |
| Deployable default (Spaces / 24 GB) | Qwen2.5-7B-Instruct | `Qwen/Qwen2.5-7B-Instruct` |
| Fallback | Llama 3.1 8B Instruct | `meta-llama/Llama-3.1-8B-Instruct` |

**[ASSUMPTION — flagged for investigation, not settled]:** newer instruct families released after this decision's information horizon (e.g. a Qwen3-generation instruct line) may outperform Qwen2.5 on long-context legal reasoning. Before the first paid training run, run the eval suite (§7) against one candidate successor. Do not churn the base on speculation — only on eval results.

## 5. Training data composition (as designated by the principal)

| Corpus | Source of truth | Role in training |
|---|---|---|
| **A — BC Statutes** | **BC Laws portal only** (bclaws.gov.bc.ca), current *and* historical consolidations | Never memorized as truth. Used to build instruction pairs where the statute excerpt is **in the context window** of the training example, with currency metadata attached. |
| **B — RTB decisions** | CanLII (published BCRTB subset) | Fact-pattern → issues → held → sections *as cited*, with pins re-mapped against BC Laws before becoming labels. |
| **C — Judicial review** | CanLII (BCSC / BCCA / SCC reviewing RTB and admin tribunals) | Standard of review, procedural fairness, Vavilov-era framing, JRPA mechanics. |

**Mandatory metadata on every statute chunk** (training or inference): enactment, citation, `bclaws_url`, `currency_line`, `accessed_on`, `version_kind` (current_consolidated / point_in_time), `event_date`, `section_ids`. No chunk trains or serves without it.

## 6. Assumptions requiring investigation (flagged, unverified)

Per the analytical discipline, the following are **ASSUMPTIONS**, not settled facts:

1. **CanLII licence.** CanLII's Terms of Use restrict bulk reproduction and scraping. Whether Corpora B and C may lawfully be harvested into a training set at the intended scale requires a licence review before ingestion. Do not scrape first and ask later.
2. **RTB publication bias.** Most RTB decisions are never published; the CanLII subset is non-random. Training on it risks teaching the model a skewed picture of arbitral outcomes. Treat published decisions as *illustrative precedent patterns*, not as the statistical distribution of RTB outcomes.
3. **King's Printer copyright.** BC Laws content carries Crown copyright conditions on reproduction. Private-use reproduction is broadly permitted; embedding consolidations in a commercial product or dataset release needs the licence terms checked.
4. **HF Space demo scope.** The public demo Space performs no inference and hosts no weights; adding a live 7B/LoRA inference tab requires ZeroGPU quota and a private-duplicate option before any real matter text is ever processed.

## 7. Success criteria (unchanged, restated)

- Zero statute quotes without BC Laws metadata in the eval suite.
- Historical-vs-current statute tests pass (event-dated analysis retrieves point-in-time text).
- RTB decision citations resolve on CanLII or are marked `[UNVERIFIED]`.
- Section-number regression tests pass (quiet enjoyment = s. 28, not s. 22; contracting-out = s. 5, not s. 6).
- Human counsel review before any "file this" output is treated as final.

## 8. Boundary

This framework produces **legal information and drafting support, not legal advice**. The principal is a self-represented litigant; any matter engaging filing deadlines, stays, or judicial review grounds warrants the `[INDEPENDENT COUNSEL RECOMMENDED]` flag. No unverified authority is ever presented as settled.
