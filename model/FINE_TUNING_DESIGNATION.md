# Fine-Tuning Designation — BC Legal AI

**Decision authority:** Principal (2026-07-21)

**Status:** Binding for Phase 1–2; revisit on hardware/licence/eval grounds.

**Character:** Engineering and legal-information infrastructure design — not legal advice.

## Core principle

The adapter's job is **behaviour, not truth**:

- Enforce analytical-tag discipline (FACT / ALLEGATION / LEGAL ARGUMENT / INFERENCE / ASSUMPTION)
- Refuse to invent pinpoints; emit `[UNVERIFIED]` when context is absent
- Handle dual current/historical statute framing
- IRAC structure, counsel-register vs. SRL plain-language register switching
- Fail-closed behaviour: when no BC Laws excerpt is in context, say so rather than recite

Statutory truth is **retrieved**, never recalled. This is RAG-first / LoRA-second.

## Assumptions flagged for investigation

1. **CanLII licence.** Bulk training corpus requires terms review; don't assume scraping is authorized.
2. **RTB publication bias.** Published decisions are selection-biased; don't treat them as population representative.
3. **King's Printer copyright.** Crown copyright on BC Laws; verify private-product reproduction terms.
4. **HF Space inference.** Public Space performs no inference. Adding live inference needs ZeroGPU quota + private Space duplicate.
5. **Successor models.** Qwen3 or later instruct family may outperform Qwen2.5; evaluate before committing to paid training.
