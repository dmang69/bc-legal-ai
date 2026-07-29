# Hugging Face Models

Model and adapter publishing workspace.

## Current model posture

- RAG-first; LoRA/QLoRA only after retrieval and evaluation gates.
- Statute truth comes from BC Laws retrieval, not weights.
- No public model should be represented as a legal authority.
- `Dmang69/bc-legal-ai-base` is treated as documentation-only unless it contains a complete standard checkpoint.
- A policy card is not a Transformers architecture; `bc_legal_ai_policy_card` must never be used as `model_type`.
- The selected deployable base is `Qwen/Qwen2.5-7B-Instruct`, pinned to a reviewed immutable revision.
- Loading must use standard Transformers classes with `trust_remote_code=False`.

## Future model targets

Potential repos:

```text
dmang69/bc-legal-ai-qwen2.5-7b-lora
dmang69/bc-legal-ai-qwen2.5-14b-lora
dmang69/bc-legal-ai-eval-baselines
```

## Required before publishing adapters

- Lawful dataset acquisition review.
- Dataset card.
- Model card.
- Evaluation suite.
- Confidential-data scan.
- Copyright/licence review for BC Laws, CanLII, RTB materials.
- Clear disclaimer: legal information only, verified retrieval required.
