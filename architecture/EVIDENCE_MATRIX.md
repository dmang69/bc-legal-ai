# Evidence Matrix — Layer 2

**Selected build path:** Option A (2026-07-21)  
**Purpose:** Factual backbone for arguments, contradictions, corroboration, gaps, and chronology.  
**Status:** Runtime store + cross-ref helpers (no OCR yet). Privilege fields on every row (see `PRIVILEGE.md`).

## Canonical row schema

| Field | Type | Description |
| --- | --- | --- |
| evidence_id | UUID | Internal immutable ID |
| matter_id | UUID / string | Partition key (privilege boundary) |
| source_file | string | Original filename |
| file_hash | SHA‑256 | Integrity + chain of custody |
| privilege_state | enum | UNCLAIMED / CLAIMED / ASSERTED / UPHELD / WAIVED / PIERCED |
| privilege_basis | enum | solicitor_client / litigation / settlement_implied / none |
| evidence_type | enum | photo, contract, notice, correspondence, official_order, financial, transcript, audio, video_frame, other |
| date_captured | datetime | EXIF or inferred |
| date_received | datetime | System ingestion timestamp |
| parties_referenced | string[] | Extracted via NER (manual/heuristic for now) |
| location_referenced | string | Property address or venue |
| claim_tags | string[] | auto‑tagged legal issues (mold_hazard, retaliatory_eviction, non_repair, etc.) |
| contradicts | UUID[] | Evidence IDs that conflict |
| corroborates | UUID[] | Evidence IDs that reinforce |
| hearing_relevance | float | 0.0–1.0 |
| admissibility_flag | enum | likely_admissible / questionable / inadmissible / needs_verification |
| ocr_confidence | float | 0.0–1.0 |
| human_notes | text | Lawyer/paralegal annotations |
| chain_of_custody | jsonb | append‑only event log |
| privilege_lock | boolean | If true → cannot be exported without privilege gate |

Implementation: `architecture.schemas.EvidenceItem` · store: `backend.evidence.matrix.EvidenceMatrix`.

## What it powers

| Downstream | How matrix is used |
|------------|-------------------|
| Arguments | `claim_tags` + evidence IDs → `LegalArgument.factual_predicate` |
| Contradictions | `contradicts[]` edges + temporal conflict detection |
| Chronology | Sort by `date_captured` / filename timestamps |
| Hearing binder | Numbered rows with relevance + notes |
| Gaps | Claim tags with zero supporting rows |
| Privilege export | `privilege_lock` / protected state → production gate |

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
Matrix rows carry `privilege_state` / `privilege_basis` / `privilege_lock` at ingest.
