# Evidence Matrix — Layer 2

**Selected build path:** Option A (2026-07-21)  
**Purpose:** Factual backbone for arguments, contradictions, corroboration, gaps, and chronology.  
**Status:** Runtime store + cross-ref helpers (no OCR yet). Privilege tags attach at ingest (see `PRIVILEGE.md`).

## What it powers

| Downstream | How matrix is used |
|------------|-------------------|
| Arguments | `claim_tags` + evidence IDs → `LegalArgument.factual_predicate` |
| Contradictions | `contradicts[]` edges + temporal conflict detection |
| Chronology | Sort by `date_captured` / filename timestamps |
| Hearing binder | Numbered rows with relevance + notes |
| Gaps | Claim tags with zero supporting rows |

## Matter isolation

```
matters/{matter_id}/
  evidence/
    matrix.jsonl          # one EvidenceItem JSON per line
    originals/            # immutable byte copies (gitignored)
    derived/              # OCR/text layers only (never overwrite originals)
```

All queries take `matter_id`. No ambient cross-matter load.

## Cross-reference engine (Phase 1)

| Detector | Trigger |
|----------|---------|
| Gap claims | Claimed tag with no evidence row |
| Corroboration | Shared claim_tag + same location (manual or keyword) |
| Contradiction | Explicit link, or temporal conflict on same claim_tag |
| Temporal conflict | Same claim_tag; dates disagree with "fixed by X" narrative (heuristic) |

OCR, EXIF, and full NER remain Layer 1 Phase 2.

## Option B (deferred)

Privilege classifier training data & annotation → higher privilege accuracy.  
Matrix rows already carry hooks for `PrivilegeMetadata` at ingest; classifier corpus is the next parallel safety track.
