# Model designation

| Document | Role |
|----------|------|
| **[BASE_MODEL_DECISION.md](BASE_MODEL_DECISION.md)** | Base model family + RAG-first architecture |
| **[FINE_TUNING_DESIGNATION.md](FINE_TUNING_DESIGNATION.md)** | Full FT rejected; **QLoRA** + retrieval-augmented instruction pairs selected |
| **[data-pipeline.md](data-pipeline.md)** | BC Laws / CanLII ingest gates and pair build stages |

## Snapshot

| Choice | Designation |
|--------|-------------|
| Primary base | `Qwen/Qwen2.5-14B-Instruct` |
| Deploy default | `Qwen/Qwen2.5-7B-Instruct` |
| Adaptation | **QLoRA** instruction SFT (not full FT) |
| Training pairs | Retrieval-augmented legal Q&A (statute in context) |
| Statute truth | **BC Laws only** (never weights) |
| RTB + JR corpus | CanLII / official courts (licence review required) |
| Pattern | **RAG-first · LoRA-second** |

Adapter trains **behaviour** (tags, fail-closed, IRAC, register).  
Statutory **truth** is always retrieved with currency metadata.
