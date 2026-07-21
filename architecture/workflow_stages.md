# Controlled associate workflow

Stages run in order. Outputs of each stage are reviewable artifacts (JSON / markdown), not a single opaque model dump.

| # | Stage | Primary agent | Human gate? |
|---|-------|---------------|-------------|
| 1 | Intake | Intake Associate | Optional |
| 2 | Conflict / party-name check | Intake Associate | Yes if conflict |
| 3 | Jurisdiction | Intake Associate | — |
| 4 | Limitation / deadline analysis | Procedural Clerk | Yes to finalize dates |
| 5 | Record ingestion | Evidence Analyst | — |
| 6 | Fact extraction | Evidence Analyst | Yes: allegation→fact |
| 7 | Procedural chronology | Evidence Analyst | — |
| 8 | Issue identification | Research Counsel | — |
| 9 | Legal research | Research Counsel | — |
| 10 | Authority verification | Citation Clerk | Court-ready block |
| 11 | Apply law to facts | Drafting Counsel | — |
| 12 | Counterargument | Devil’s Advocate | — |
| 13 | Remedy analysis | Drafting Counsel | — |
| 14 | Drafting | Drafting Counsel | — |
| 15 | Citation audit | Citation Clerk | Court-ready block |
| 16 | Evidence audit | Evidence Analyst | — |
| 17 | Procedural-compliance audit | Procedural Clerk | — |
| 18 | Human approval | Supervising Counsel Gate | **Required** |
| 19 | Export | Export engine | Yes before file/send |

See `schemas.py` for `AuthorityStatus`, `Proposition`, and `ReviewReport`.
