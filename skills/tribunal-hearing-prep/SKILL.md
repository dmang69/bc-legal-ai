---
name: tribunal-hearing-prep
description: "Use when preparing for BC tribunal hearings or judicial review of tribunal decisions: record dissection, legal test, binders, outlines, witness prep, Q&A simulation."
version: 1.0.0
author: BC Legal AI Associate
license: MIT
metadata:
  hermes:
    tags: [legal, bc, tribunal, hearing, witness, rtb, bchrt, judicial-review, record]
    related_skills:
      - bc-judicial-review-guide
      - bc-tenancy-procedure
      - administrative-law-canada
      - evidence-law-canada
      - critical-reading
      - supreme-court-civil-counsel
---

# Tribunal hearing preparation (BC)

**Legal information only — not legal advice.**  
Not a rehearing of the merits unless the forum is a first-instance hearing.  
**JR is not a new trial.** Record-bound. Verify statutes on **BC Laws**, Rules, and tribunal practice directions before reliance.

Supports:

| Forum track | Typical use |
|-------------|-------------|
| **RTB first-instance** | Dispute Resolution hearing (phone/video/written) |
| **BCHRT** | Human rights hearing / pre-hearing conference |
| **Tribunal → BCSC JR** | Form 66 petition hearing on the **record** |
| **Other ATA tribunals** | Same structure; map standard of review carefully |

## Locked product rules

1. Consent ≠ privilege.  
2. Form **66** petition; Form **67** response; interlocutory ≈ **32/33**; affidavit **109**.  
3. JR clock: **60 days from issuance** of final decision when ATA s.57 applies — alternatives when uncertain.  
4. RTB archive is partial — absence ≠ non-existence.  
5. Every material **FACT** needs a record pin or **ALLEGATION** tag.  
6. No autonomous filing/service/settlement. Human owns hearing day strategy.

---

## Workflow map (structured options)

### A — Dissect the record and the law

| Step | Action | Output tags |
|------|--------|-------------|
| A1 | **Read the whole record** — decision, reasons, transcripts/notes, exhibits, correspondence | `RECORD_MAP` |
| A2 | Spot **factual errors** (findings vs evidence) | `FACT_ERROR_LOG` |
| A3 | Spot **procedural unfairness** (notice, participation, secret evidence, bias cues) | `FAIRNESS_LOG` |
| A4 | Identify **legal test / standard of review** (e.g. patent unreasonableness ATA s.58 for RTB JR; correctness for fairness) | `LEGAL_TEST` |
| A5 | Map **governing legislation** (BC Laws links only — no statute text from memory) | `STATUTE_MAP` |
| A6 | Compare **similar tribunal/court outcomes** as research plan (verify on CanLII) | `AUTHORITY_PLAN` |

### B — Organize materials

| Step | Action | Output tags |
|------|--------|-------------|
| B1 | Build **tabbed binder index** (physical or digital) | `BINDER_INDEX` |
| B2 | Paginate / Bates-style labels; **pinpoint** decision paragraphs and exhibit tabs | `PAGINATION` |
| B3 | Draft **opening statement** (2–4 min spine) | `OPENING` |
| B4 | List **core facts** (numbered, pinned) | `CORE_FACTS` |
| B5 | Draft **concise legal submissions** (issue → test → apply record → remedy) | `SUBMISSIONS` |

### C — Witnesses and arguments

| Step | Action | Output tags |
|------|--------|-------------|
| C1 | Identify witnesses: **must / helpful / do not call** | `WITNESS_LIST` |
| C2 | Coach: answer only what is asked; “I don’t recall” > guess; personal knowledge | `WITNESS_COACH` |
| C3 | **Simulate tribunal Q&A** and opposing cross | `QA_SIM` |
| C4 | Pre-butt **hard questions** and honesty scripts | `HARD_Q` |
| C5 | Day-of checklist (exhibits open, quiet room, accommodations) | `DAY_OF` |

### D — JR-specific (when reviewing a tribunal decision)

| Step | Action |
|------|--------|
| D1 | Finality / issuance date candidates → JR clock (HITL) |
| D2 | Grounds matrix: fairness (correctness) vs patent unreasonableness |
| D3 | Form 66 skeleton + Form 109 exhibit plan |
| D4 | Remedy: quash / remit / stay (RJR three-part if stay) |

---

## Module 1 — Reviewing the record

**Goal:** every page read once for errors; second pass for theory.

### Checklist

- [ ] Decision + reasons (paragraph numbers)  
- [ ] Notices and service proofs  
- [ ] Party evidence packages as filed **below**  
- [ ] Transcript / recording notes / arbitrator notes (if available)  
- [ ] Prior interim orders / reviews affecting finality  

### Error spotting prompts (for AI + human)

1. Finding of fact with **no record support** → mark.  
2. Finding **contradicted** by uncontested exhibit → mark.  
3. Relevant evidence **ignored** → mark with pin.  
4. Procedure: notice period; participation; interpreter; accommodation.  
5. Reasons fail to explain the path from evidence to result.

**Label outputs:**

```text
FACT — [pin: decision para / Tab X p.Y]
ALLEGATION — [not yet pinned]
ASSUMPTION — [to verify]
ARGUMENT — [legal theory]
```

---

## Module 2 — Studying the legal test

### First-instance tribunal (e.g. RTB)

- Issue → RTA / MHPTA sections (verify BC Laws)  
- Burden of proof / onus as applicable  
- Policy guidelines (RTB) — secondary only; statute wins  

### Judicial review of tribunal (BCSC)

| Question | Working standard (RTB/ATA path — verify) |
|----------|------------------------------------------|
| Fact / mixed / many law questions inside expertise | **Patent unreasonableness** (ATA s.58(2)(a)) |
| Procedural fairness | **Correctness** |
| True jurisdiction / central importance carve-outs | **Correctness** (careful framing) |

**Do not** re-argue pure credibility preference without a record-based fairness or patent-unreasonableness hook.

---

## Module 3 — Building a tabbed binder

### Suggested RTB / JR digital binder tabs

| Tab | Contents |
|-----|----------|
| 1 | Index + chronology |
| 2 | Decision under review (or claim/application) |
| 3 | Notices / pleadings / applications |
| 4 | Party evidence (your side) |
| 5 | Opposing evidence |
| 6 | Transcript / hearing notes |
| 7 | Legislation extracts (official BC Laws print) |
| 8 | Authorities (CanLII PDFs — cases only) |
| 9 | Opening + submissions outline |
| 10 | Witness scripts + hard Q list |

Use **coloured tabs** or PDF bookmarks. Page-turn speed > pretty formatting.

### Binder index template

```text
TAB | LABEL | PAGE RANGE | KEY PINS
1 | Index/Chronology | 1–n | —
2 | Decision | … | paras X–Y
...
```

---

## Module 4 — Drafting the outline

### Opening (structure)

1. Who you are / who you represent (role honesty)  
2. Decision/date/file (or claim)  
3. **One sentence** issue  
4. **Two strongest points** + remedy sought  
5. Roadmap (fairness / patent unreasonableness / facts)  

### Core facts list

Numbered; each line ends with `(Tab # / pin)`.  
No new evidence on JR unless exception is properly framed.

### Legal submissions spine (IRAC-light)

```text
ISSUE
TEST / STANDARD (with statute pin — verify BC Laws)
APPLICATION (record pins only)
REMEDY (precise: quash+remit / dismiss / stay conditions)
```

---

## Module 5 — Coaching witnesses

### Rules to give the witness (plain language)

1. Answer only the question asked.  
2. “I don’t know / I don’t recall” is better than guessing.  
3. Personal knowledge only — do not speculate.  
4. Pause is OK. Ask for the question again if needed.  
5. Stay calm; do not argue with the tribunal or other party.  
6. Documents: wait until directed; use the **tab number**.  

### Ethical bounds (platform)

- Do not script false testimony.  
- Do not coach to conceal relevant truth.  
- Flag when **independent counsel** is needed (eviction, complex fairness, clock risk).

---

## Module 6 — Simulating Q&A

### Tribunal / panel style questions

- “Where in the record is that?”  
- “What order do you want today?”  
- “Why isn’t this just reweighing credibility?”  
- “What is the standard of review for this ground?”  
- “What prejudice if we grant/dismiss a stay?”  

### Cross-style (opposing party)

- Inconsistent prior statements  
- Missing documents  
- Motive / interest  
- Hearsay “who told you?”  

### Output format for sim

```text
Q: …
A (honest, pinned): …
TRAP: …
RECOVERY: …
```

---

## Tribunal-type quick map (BC)

| Type | First stop skill | Hearing focus |
|------|------------------|---------------|
| **RTB** | `bc-tenancy-procedure` + this skill | Evidence tabs, RTA issues, participatory hearing |
| **BCHRT** | `bc-tenancy-advocacy` (human rights notes) + this skill | Discrimination elements; accommodations |
| **JR of RTB** | `bc-judicial-review-guide` + this skill | Record-bound; Form 66; standard of review |
| **Other** | `administrative-law-canada` + this skill | Enabling Act + fairness |

---

## Slash / specialist usage

- Specialist: **`hearing_prep`**  
- Chat cues: “hearing prep”, “binder”, “witness coach”, “tribunal Q&A”, “dissect the decision”  
- OpenClaw: tools `hearing_record_map`, `hearing_binder_index`, `hearing_outline`, `hearing_witness_qa`  

## Output package (when user asks for full prep)

1. `RECORD_MAP` + error/fairness logs  
2. `LEGAL_TEST` + statute verification list (BC Laws URLs)  
3. `BINDER_INDEX`  
4. `OPENING` + `CORE_FACTS` + `SUBMISSIONS`  
5. `WITNESS_COACH` + `QA_SIM`  
6. Disclaimer + counsel flag if high stakes  

## Verification checklist

- [ ] Whole record considered (or gaps listed)  
- [ ] Standard of review / legal test stated correctly for forum  
- [ ] Binder index complete; pins work  
- [ ] Opening ≤ ~4 minutes spoken  
- [ ] Witness rules shared; no false-scripting  
- [ ] Hard Q list rehearsed  
- [ ] BC Laws / CanLII verification still required  
- [ ] **Not legal advice** footer  
