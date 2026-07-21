# GroundingGate

## Citation record

```
Citation {
  citation_id, type: STATUTE|REGULATION|CASE_LAW|RULE|POLICY
  // statutes: jurisdiction, act, section, subsection, exact_text (from BC Laws only)
  // cases: case_name, citation, principle_established, parenthetical
  // verification: source_url, last_verified, verifying_hash, superseded_by
  // usage: applies_to[], jurisdiction_scope
  status: VERIFIED|…   // VERIFIED required for grounding
}
```

`exact_text` must be pasted from official BC Laws (or equivalent) at verification — never invented.
`CIT-RTA-S56` is seeded as **PARTIALLY_VERIFIED** (structure only) until section wording is re-checked on BC Laws.

Every claim in system output must carry:

| Element | Requirement |
|---------|-------------|
| `factual_basis` | `EvidenceNode.node_id` that exists in the matter graph |
| `legal_basis` | `Citation` resolved **VERIFIED** in citation DB |
| `inference_chain` | ≥2 explicit steps connecting fact → law → conclusion |

## Refusal messages

| Missing | Response |
|---------|----------|
| factual basis | `REFUSE_OUTPUT` — No evidence supports this claim. Add evidence or revise query. |
| legal basis | `REFUSE_OUTPUT` — No legal authority found. Search knowledge base or flag for human. |
| inference chain | `REFUSE_OUTPUT` — Logical gap between evidence and conclusion. Review inference steps. |
| unverified cite | `REFUSE_OUTPUT` — Legal authority is UNVERIFIED… |

```python
from architecture.grounding import Citation, GroundedClaim, InferenceStep
from backend.matters import create_matter

s = create_matter("M", matter_id="m1")
# ... ingest evidence nodes ...
result = s.ground_claim(GroundedClaim(
    claim="Landlord failed to repair mold",
    factual_basis="EV-2026-000147",
    legal_basis=Citation(short_cite="RTA s. 32", section="32"),
    inference_chain=[
        InferenceStep(statement="Photos show mold", premise_type="fact",
                      supports_from=["EV-2026-000147"]),
        InferenceStep(statement="RTA s. 32 requires repair", premise_type="law"),
        InferenceStep(statement="Therefore repair obligation engaged", premise_type="conclusion"),
    ],
))
if not result.allowed:
    print(result.refuse_text())
```
