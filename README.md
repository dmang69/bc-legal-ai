# BC Legal AI — Counsel Workbench

Research and drafting workbench for **British Columbia civil / administrative litigation**, with a focus on superior court practice and Residential Tenancy Branch (RTB) judicial review pathways.

> **Not legal advice.** All outputs require licensed counsel review before filing or reliance.

## Skills

| Skill | Path | Use |
|-------|------|-----|
| **supreme-court-civil-counsel** | [`skills/supreme-court-civil-counsel/`](skills/supreme-court-civil-counsel/) | Primary mandate: analysis, drafting, quality control |
| **bc-judicial-review-guide** | [`skills/bc-judicial-review-guide/`](skills/bc-judicial-review-guide/) | JR procedure & standards |
| **bc-tenancy-substantive** | [`skills/bc-tenancy-substantive/`](skills/bc-tenancy-substantive/) | RTA doctrine scaffold |
| **bc-tenancy-procedure** | [`skills/bc-tenancy-procedure/`](skills/bc-tenancy-procedure/) | RTB process scaffold |
| **canlii-boa-builder** | [`skills/canlii-boa-builder/`](skills/canlii-boa-builder/) | Verified authorities / BOA |

Full professional framework: [`skills/supreme-court-civil-counsel/counsel-framework.md`](skills/supreme-court-civil-counsel/counsel-framework.md)

## Always separate

**FACT · ALLEGATION · LEGAL ARGUMENT · INFERENCE · ASSUMPTION · PROCEDURAL HISTORY · RECOMMENDATION**

And in documents: **FACT / LAW / ARGUMENT / ANALYSIS / REMEDY**

## Quick start for agents

1. Read `supreme-court-civil-counsel/SKILL.md` + `counsel-framework.md`.  
2. For RTB/JR, load the companion skills.  
3. Extract facts only from the record; label categories.  
4. Verify every citation (CanLII) before treating as filing-ready.  
5. Use [`templates/document-skeleton.md`](templates/document-skeleton.md).  
6. Run [`checklists/decision-review.md`](checklists/decision-review.md) on target decisions.  

## Matters

Place case-specific materials under `matters/<style-or-short-name>/`.

## GitHub

Target remote (create if missing): `https://github.com/dmang69/bc-legal-ai`
