# BC Civil Litigation Skill Pack

## Purpose

Doctrine-heavy skills for **research, issue-spotting, document drafting, and hearing preparation** on BC superior-court and RTB → judicial review matters.

**Not legal advice.** Legal information and drafting support only. Verify authorities and current statutes before filing.

**Version note (2026-07):** `supreme-court-civil-counsel` **v2.1** locks Role & Analytical Framework language (senior multi-discipline counsel standard; strict FACT/ALLEGATION/… labels; jurisdiction-first + full legislation map; SRL boundary). `bc-judicial-review-guide` **v2.0** locked design corrections (Form 66/67/32/33/109, ATA s.57 clock, ATA s.58 patent unreasonableness for RTB, consent≠privilege, incomplete RTB archive, honest encryption). **`counsel-research-draft-pipeline` v1.0** ordered five-step production pipeline.

---

## Core counsel stack (load first on court work)

| Skill | Role |
|-------|------|
| **`counsel-research-draft-pipeline`** | Ordered production: research/verify → fact–law → counters → draft format → quality review + human release gate |
| **`supreme-court-civil-counsel`** | Elite drafting frame, category labels, citation gate, deliverables, quality review |
| **`bc-judicial-review-guide`** | RTB/tribunal → BCSC JR: ATA s.58, Form 66, s.57 clock, stays, fairness, service |
| `counsel-framework.md` (pipeline + supreme-court-civil-counsel) | Expanded professional mandate |

---

## Tenancy foundation

| Skill | Role |
|-------|------|
| `bc-tenancy-substantive` | RTA / MHPTA substance |
| `bc-tenancy-procedure` | RTB process, notices, timelines, service at tribunal level |
| `bc-tenancy-advanced` / `bc-tenancy-advocacy` | Advanced / advocacy modules if present |

---

## Doctrine pack

| Skill | Role |
|-------|------|
| `legal-terminology-core` | Glossary + consistent labeling language |
| `evidence-law-canada` | Affidavits, exhibits, hearsay, privilege, authenticity |
| `statutory-interpretation` | Modern Canadian text-context-purpose |
| `administrative-law-canada` | Broader admin doctrine (use with ATA s.58 for RTB — do not erase statute) |
| `canlii-boa-builder` | Verified CanLII cites + Book of Authorities packaging |
| `critical-reading` | Decision / affidavit dissection |

---

## How to route assignments

### Superior court drafting (non-JR or general civil)

1. `counsel-research-draft-pipeline` (enforce Steps 1–5)  
2. `supreme-court-civil-counsel`  
3. `evidence-law-canada` if affidavit-heavy  
4. `statutory-interpretation` if statutory fight  
5. `canlii-boa-builder` before any BOA / cited brief

### RTB judicial review

1. `bc-tenancy-substantive` + `bc-tenancy-procedure`  
2. `bc-judicial-review-guide` (standard of review + Form 66 + clock)  
3. `counsel-research-draft-pipeline` + `supreme-court-civil-counsel`  
4. `evidence-law-canada` + `canlii-boa-builder`  
5. Case-specific skill if present (e.g. matter strategy)

### Decision audit only

`critical-reading` → `bc-judicial-review-guide` Module 3 grounds matrix → counsel labels

---

## Locked corrections (all skills must respect)

1. Consent is not privilege.  
2. Consent withdrawal is not unconditional deletion (PIPA).  
3. Form **66** starts a petition; Form **67** responds; interlocutory **32**/**33**; affidavit **109**.  
4. JR: **60 days from issuance** of final decision (ATA s.57(1)); s.57(2) extensions; **alternatives** when uncertain.  
5. Honest encryption claims only.  
6. RTB archive is a **published subset** only.

---

## Public demo

Static HF Space mirrors triage / JR clock / tagger / guardrails:  
https://huggingface.co/spaces/Dmang69/bc-legal-ai-demo  

Source: `huggingface-space-static/`

---

## Editing rules

- Prefer patching existing skills over spawning near-duplicates.  
- Keep SKILL.md bodies process-heavy; put long doctrine in `references/` if a skill grows past ~20k chars.  
- Never invent form numbers or limitation rules that contradict the locked table without an explicit `[LAW CURRENCY UNVERIFIED]` note and BC Laws task.  
