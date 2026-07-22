# Base Model Decision — BC Legal AI

**Decision authority:** Designated by the principal (2026-07-21)

**Date:** 2026-07-21

**Status:** Binding for the workbench; revisit only on hardware, licence, or eval-driven grounds.

## The three questions

| Question | Designation |
|----------|-------------|
| Full fine-tune? | **Rejected** as primary method. |
| LoRA? | **Selected.** QLoRA adapters, instruction-tuned. |
| Instruction tuning on legal Q&A pairs? | **Selected** as the dataset format for the LoRA SFT run — in retrieval-augmented form. |

**One-line designation:**

> LoRA instruction tuning on retrieval-augmented legal Q&A pairs, on a Qwen2.5-Instruct base, with BC Laws as the sole statutory source of truth at both training-label time and inference time.

## Base model selection

| Role | Model | HF ID |
|------|-------|-------|
| Primary base | Qwen2.5-14B-Instruct | `Qwen/Qwen2.5-14B-Instruct` |
| Deployable default (Spaces / 24 GB) | Qwen2.5-7B-Instruct | `Qwen/Qwen2.5-7B-Instruct` |
| Fallback | Llama 3.1 8B Instruct | `meta-llama/Llama-3.1-8B-Instruct` |

## Why LoRA, not full fine-tune

1. **Currency failure.** Legislation mutates. A full fine-tune bakes today's RTA into weights and decays immediately. LoRA adapter stays small and updatable.
2. **Catastrophic forgetting.** Full FT on narrow BC tenancy corpus degrades general instruction-following. LoRA preserves base competence.
3. **Cost asymmetry.** Full FT: multi-GPU, repeated runs. QLoRA: single 24–48 GB card, adapter-only versioning.
4. **Auditability.** LoRA adapter is a small, diff-able artifact. When a regression appears, retrain the adapter in hours—not the base in days.

## Training data composition

| Corpus | Source of truth | Role in training |
|--------|---|---|
| **A — BC Statutes** | **BC Laws portal only** | Never memorized. Used to build instruction pairs where statute excerpt is **in the context window** with currency metadata. |
| **B — RTB decisions** | CanLII (published subset) | Fact-pattern → issues → held → sections cited, pins re-mapped against BC Laws before becoming labels. |
| **C — Judicial review** | CanLII (BCSC / BCCA / SCC) | Standard of review, procedural fairness, Vavilov, JRPA mechanics. |

**Mandatory metadata on every statute chunk:**

```text
enactment
citation
bclaws_url
currency_line
accessed_on
version_kind (current_consolidated / point_in_time)
event_date
section_ids
```

## Success criteria

- ✅ Zero statute quotes without BC Laws metadata in the eval suite.
- ✅ Historical-vs-current statute tests pass.
- ✅ RTB decision citations resolve on CanLII or marked `[UNVERIFIED]`.
- ✅ Section-number regression tests pass (quiet enjoyment = s.28, not s.22).
- ✅ Human counsel review before any "file this" output.

## Assumptions flagged for investigation

1. **CanLII licence.** Bulk reproduction for training requires licence review (do not scrape first, ask later).
2. **RTB publication bias.** Published decisions are non-random; don't teach the model skewed outcomes.
3. **King's Printer copyright.** Crown copyright on BC Laws; verify reproduction conditions before release.
4. **HF Space demo scope.** Public demo performs no inference; adding live inference requires ZeroGPU quota and private duplicate.
