# Legal knowledge graph (GraphRAG)

## Nodes

Person · Party · Lawyer · Case · Tribunal File · Court File · Document · Evidence Item · Fact · Allegation · Event · Issue · Statute · Section · Authority · Legal Test · Procedural Step · Deadline · Ground of Review · Remedy

## Edges

| Edge | Use |
|------|-----|
| SUPPORTS | Evidence or authority supports a proposition |
| CONTRADICTS | Direct conflict between sources or propositions |
| CITED_BY | Citation relationship |
| DECIDED_IN | Outcome in a proceeding |
| SUBMITTED_AT | Filing venue/time |
| SERVED_ON | Service relationship |
| OCCURRED_BEFORE | Temporal order |
| APPLIES_TO | Norm applies to issue/facts |
| DISTINGUISHES | Authority distinguished |
| OVERRULES | Authority overruled |
| AMENDS | Statutory or order amendment |
| EVIDENCE_FOR / EVIDENCE_AGAINST | Evidentiary polarity |
| REQUIRES_VERIFICATION | Soft edge until Citation Clerk clears |

## Example queries

- Show every document supporting the proposition that the unit was legally identified as 990A before the 2025 hearing.  
- Identify every contradiction between counsel’s submissions, the sworn representative’s evidence, and the written decision.
