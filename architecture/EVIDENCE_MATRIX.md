# Evidence Matrix — Layer 2

**Selected build path:** Option A (2026-07-21)  
**Purpose:** Factual backbone for arguments, contradictions, corroboration, gaps, and chronology.  
**Status:** Runtime store + cross-ref helpers (no OCR yet). Privilege fields on every row (see `PRIVILEGE.md`).

## EvidenceNode (graph unit)

Canonical graph node: `architecture/evidence_node.py` · store: `backend/evidence/nodes.py`.

| Field | Notes |
| --- | --- |
| `node_id` | Sequential immutable `EV-YYYY-NNNNNN` |
| `doc_hash` | `sha256:…` of source file |
| `privilege_class` | OPEN / PROTECTED / RESTRICTED / WAIVED (Layer 0) |
| `source_type` | PHOTO, EMAIL, RTB_DECISION, LEASE_AGREEMENT, … |
| `date_created` / `date_received` / `date_entered_system` | ISO timestamps |
| `custodian` | Who produced/possesses |
| `authenticity_status` | VERIFIED / DISPUTED / UNVERIFIED |
| `hearsay_flag` / `hearsay_exception` | Assessment fields (not court findings) |
| `best_evidence_rule` | ORIGINAL / CERTIFIED_COPY / PHOTOCOPY / DIGITAL |
| `extracted_text` / `key_facts` / `entities_mentioned` | Semantic layer |
| `corroborates` / `contradicts` / `causally_linked_to` | Node ID edges |
| `temporal_sequence` | `{ before: [], after: [] }` |
| `chain_of_custody` / `alteration_history` | Provenance |
| `exhibit_number` / `admissibility_assessment` | Hearing readiness |

Matrix rows (`EvidenceItem`) remain the ingest ledger; nodes are the graph view with sequential IDs.

## Canonical matrix row schema

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
| **Key-fact contradiction** | Shared `fact_key` with conflicting `value` → CONTRADICTS + warning + report |

### Key-fact contradiction algorithm

```
FOR each pair of EvidenceNodes (A, B):
    IF A.key_facts ∩ B.key_facts ≠ ∅:        // shared fact_key
        FOR each shared fact f:
            IF A.value(f) conflicts with B.value(f):
                CREATE edge(A → B, type=CONTRADICTS)
                FLAG both nodes with contradiction_warning
                GENERATE ContradictionReport {
                    fact, node_a_claim, node_b_claim,
                    resolution_strategy: A_PRIORITY | B_PRIORITY | NEEDS_HUMAN | BOTH_RELEVANT,
                    weight_difference: |A.confidence - B.confidence|
                }
```

Implementation: `backend/evidence/contradiction_engine.py`  
Run: `EvidenceNodeStore.run_contradiction_scan()` (also via `MatterSession.analysis_report()`).

OCR, EXIF, and full NER remain Layer 1 Phase 2.

## Option B (deferred)

Privilege classifier training data & annotation → higher privilege accuracy.  
Matrix rows carry `privilege_state` / `privilege_basis` / `privilege_lock` at ingest.
