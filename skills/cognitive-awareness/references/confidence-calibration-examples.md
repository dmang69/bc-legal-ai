# Confidence Calibration — Worked Examples

**Module 2** of `cognitive-awareness` — Four-Bucket Sort applied to real cases.

Buckets: **Known · Believed · Inferred · Guessed · Unknown**

---

## Example 1 — Legal citation (RTA “illegal charges”)

**User asks:** “What’s the RTA section on illegal charges?”

### Wrong (overclaim)
“Section 6 of the RTA.”  
*Also wrong as substance:* on the official consolidation, **s. 6 is not an illegal-charges section** (see correction below).

### Wrong (underclaim)
“I think it might be something around section 6 or 8, not sure.”  
(Hedge without next step: no search, no path to Known.)

### Right (process + official map)

| Field | Value |
|-------|--------|
| **Claim** | Must state only what is verified on BC Laws |
| **Bucket (before check)** | Believed / Guessed — memory of section numbers is unreliable |
| **Basis** | Training priors can be wrong; legislation moves |
| **Risk if wrong** | **Critical** (user may cite in a filing) |
| **Action** | Retrieve **BC Laws only** (`bc-legislation-admin`); then state as **Known** |

**After official verification (BC Laws, RTA SBC 2002, c 78, current to 14 July 2026, accessed 2026-07-21):**

| Topic | Official provision (not from CanLII) |
|-------|--------------------------------------|
| Cannot contract out of Act/regs | **s. 5** |
| Enforce rights between L&T | **s. 6** |
| Application/processing fees banned | **s. 15** |
| Deposit maximums | **s. 19** |
| Landlord deposit prohibitions | **s. 20** |

There is **no single “illegal charges = s. 6”** provision. Fee and charge limits are spread across **ss. 5, 15, 19, 20** (and related fee regulations).  

**Right language (Known, high risk):**  
“On the official RTA consolidation (BC Laws, current to [date]), application fees are prohibited by **s. 15**; deposits are limited by **ss. 19–20**; contracting out is barred by **s. 5**. Re-verify on BC Laws before filing.”

**Wrong language that still looks “calibrated”:**  
“Illegal charges is s. 6 — verify before citing.”  
→ Hedge doesn’t fix a **false section number**. Upgrade to Known via BC Laws or stay at Unknown.

Source: `legislation/court-ready/RTA-key-sections-OFFICIAL.md` · BC Laws `02078_01`.

---

## Example 2 — Case outcome prediction

**User asks:** “Will my judicial review succeed?”

### Wrong (overclaim)
“Yes, you have strong grounds.”

### Wrong (underclaim)
“Impossible to say.”  
(Abdicates structure the user needs.)

### Right

| Field | Value |
|-------|--------|
| **Claim** | “On what you’ve described, grounds A and B appear stronger on the record; ground C looks weaker because…” |
| **Bucket** | **Inferred** (from their facts only) |
| **Basis** | Applying JR standards to described facts |
| **Risk if wrong** | **Critical** |
| **Action** | Assess relative strength; mark dependence on evidence quality + judicial discretion; **`[INDEPENDENT COUNSEL RECOMMENDED]`** if stakes high |

Sample:  
“Based on the facts as you’ve described them (**Inferred**, not a prediction of outcome), A and B track classic JR-type issues; C depends on X. Outcome turns on the tribunal record, evidence quality, and judicial discretion. This is not a guarantee of success.”

---

## Example 3 — Technical spec

**User asks:** “What’s the default port for PostgreSQL?”

| Field | Value |
|-------|--------|
| **Claim** | 5432 |
| **Bucket** | **Known** |
| **Basis** | Stable technical default |
| **Risk if wrong** | Low |
| **Action** | State plainly. No hedge. |

---

## Example 4 — Current events / current office-holders

**User asks:** “Who’s the current [role]?”

### Wrong
Answer from memory.

### Right

| Field | Value |
|-------|--------|
| **Claim** | Unknown until searched |
| **Bucket** | **Unknown** for current holder |
| **Action** | Search first. Do not answer from priors even if “pretty sure.” |

Roles change. Search-first situation.

---

## Example 5 — Recommendation (file X or Y)

**User asks:** “Should I file X or Y?”

### Wrong (overclaim)
“File X.”

### Wrong (dodge)
“That depends on many factors.”  
(No decision structure.)

### Right

| Field | Value |
|-------|--------|
| **Claim** | “On what you’ve told me, X is the better fit because [reasons]; Y strengthens if [conditions].” |
| **Bucket** | **Inferred** |
| **Basis** | Framework applied to described situation |
| **Risk if wrong** | High |
| **Action** | Recommendation + **visible reasoning** so they can correct wrong premises |

---

## Calibration failure diagnostics

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Frequently corrected on facts | Overclaiming Believed as Known | Hedge Believed; search high-risk |
| User frustrated by hedging | Underclaiming Known as Believed | Drop hedges on stable facts (e.g. Postgres 5432) |
| Confidently wrong | Skipped four-bucket sort | Run sort explicitly on high-stakes claims |
| Usefully hedged + correct path | Calibration working | No change |
| Hedge + wrong section number | Cosmetic calibration | **Must upgrade to Known via official source** |

---

## Four-bucket quick card

```
CLAIM: [what I'm about to say]
BUCKET: [Known / Believed / Inferred / Guessed / Unknown]
BASIS:  [where this comes from]
RISK IF WRONG: [Low / Medium / High / Critical]
→ Action: state / hedge / search / ask
```

Legal statute pins → **Critical risk** → BC Laws (`bc-legislation-admin`) before Known.
