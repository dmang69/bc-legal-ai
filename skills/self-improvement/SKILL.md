---
name: self-improvement
description: >
  Meta-learning and self-advancement. Detect gaps and corrections in real time;
  produce formal skill patches the user can install between sessions. Triggers:
  "that's wrong", "you missed", "actually", "outdated", "improve this skill",
  "update your knowledge", "learn from this", "audit this skill", "skill patch",
  "remember this", "advance yourself". Applies to all skills including itself.
---

# Self-Improvement — Meta-Learning Framework

Operates at **two levels**:

| Level | Mode |
|-------|------|
| **In-conversation** | Detect gaps and corrections in real time; draft patches immediately |
| **Between sessions** | Package formal skill patches the user can install |

**Goal:** Every conversation makes the system sharper.

> This skill improves **other skills** and **itself**. Apply Modules 1–8 to `self-improvement` when its signals or formats fail.

---

## Skill tree

| Module | Domain |
|--------|--------|
| 1 | Gap Detection — missing knowledge in real time |
| 2 | Correction Capture Protocol — formalizing when wrong |
| 3 | Knowledge Synthesis Engine — new info → skill patches |
| 4 | Skill Performance Audit — self-scoring responses |
| 5 | Cross-Skill Integration — wiring skills together |
| 6 | Version Management — what changed and why |
| 7 | Learning Trigger Vocabulary — signals that demand improvement |
| 8 | Skill Patch Format — how to write an upgrade |
| 9 | Self-Reflection Protocol — meta-cognition |
| 10 | Advancement Roadmap — systematic evolution |

---

## Module 1: Gap Detection — Real Time

Run **silently** after every response when any skill is active.

### Gap detection checklist

- [ ] **Excessive hedging** (“I think”, “possibly”) → shallow knowledge; research or skill update  
- [ ] **Missed specific rule/section/deadline/procedure** → hole in domain module  
- [ ] **Generic where specific needed** → add examples/procedures  
- [ ] **User corrected or supplied known knowledge** → Module 2  
- [ ] **Wrong skill routed / no route** → description + trigger vocabulary  
- [ ] **Follow-up that first answer should have pre-empted** → anticipatory coverage  
- [ ] **Heavy user edit / rejected output** → format, depth, or style  

### Gap classification

| Type | Description | Response |
|------|-------------|----------|
| **Factual Gap** | Missing fact, rule, section | Add to module |
| **Procedural Gap** | Missing workflow step | Add to procedure module |
| **Depth Gap** | Too shallow | Expand module |
| **Scope Gap** | Topic not covered by any skill | Propose new module/skill |
| **Trigger Gap** | Skill didn’t activate | Update description |
| **Format Gap** | Wrong output shape | Update drafting standards |
| **Integration Gap** | Skills didn’t connect | Module 5 |

---

## Module 2: Correction Capture Protocol

**Trigger:** User indicates wrong, incomplete, or outdated content.

### Trigger phrases (exact or approximate)

- “That’s not right / wrong / incorrect”  
- “You missed / forgot / left out…”  
- “Actually… / In fact… / To be more precise…”  
- “That’s outdated / changed / no longer…”  
- “The real rule is… / The actual section is…”  
- “You should also mention… / Don’t forget…”  
- “That doesn’t apply here because…”  
- Any provision, case, or deadline correction  

### Sequence

**Step 1 — Acknowledge precisely** (no vague apology):

> “Corrected — I had [X] but the accurate rule is [Y]. Capturing that now.”

**Step 2 — Classify**

```
CORRECTION LOG
──────────────
Skill affected:     [skill name]
Module affected:    [module number and name]
What was wrong:     [exact error]
What is correct:    [accurate information]
Source:             [user / cited / implied]
Correction type:    [Factual / Procedural / Depth / Scope / Trigger / Format]
Priority:           [Critical / High / Medium / Low]
```

| Priority | Meaning |
|----------|---------|
| **Critical** | Harm risk (wrong deadline, wrong legal standard) |
| **High** | Significant quality degradation |
| **Medium** | Minor / edge case |
| **Low** | Stylistic preference |

**Step 3 — Draft patch immediately** (Module 8).  
**Step 4 — Offer installable update:**

> “Here’s the updated module text. Want me to package this as a skill update you can install?”

→ `templates/correction-capture.md`

---

## Module 3: Knowledge Synthesis Engine

**Trigger:** User provides new domain info (law change, procedure, case, domain knowledge).

### Protocol

**Step 1 — Landing zone**

```
SYNTHESIS MAP
─────────────
New information:    [summary]
Landing skill:      [name]
Landing module:     [# or NEW MODULE NEEDED]
Integration type:   [Add / Replace / New module / New skill]
```

**Step 2 — Structure**

- Rule → source (section, act, policy)  
- Procedure → numbered checklist  
- Options → comparison table  
- Case → cases section with annotation  

**Step 3 — Downstream impact**

```
IMPACT SCAN
───────────
New info changes:   [what is now wrong]
Sections to update: [list]
Sections unaffected:[confirmed clean]
```

**Step 4 — Write patch** (Module 8).

→ `templates/synthesis-map.md`

---

## Module 4: Skill Performance Audit

**Trigger:** User requests audit/score, or skill performed notably well/poorly.

### Rubric (1–5 each → total /35)

| Dimension | 1 | 3 | 5 |
|-----------|---|---|---|
| Accuracy | Errors | Mostly correct | Fully accurate |
| Depth | Surface | Main points | Exhaustive |
| Triggering | Often missed | Usually OK | Always correct |
| Output format | Poor | Workable | Exact fit |
| Completeness | Major gaps | Minor gaps | None |
| Anticipation | Reactive only | Some | Pre-empts |
| Cross-linking | Isolated | Some | Integrated |

### Audit report

```
SKILL AUDIT: [skill name] — [date]
────────────────────────────────────
Overall Score:    [X/35]

Strengths:
  - …

Gaps Identified:
  - [gap] → Priority: [C/H/M/L] → Patch in: Module [X]

Trigger Accuracy:
  - False negatives: …
  - False positives: …
  - Description update needed: yes/no

Recommended Actions (priority order):
  1. …
```

→ `templates/audit-report.md`

---

## Module 5: Cross-Skill Integration

**Trigger:** Two+ skills needed, or one skill would improve by referencing another.

```
INTEGRATION MAP
───────────────
Skill A:            [name]
Skill B:            [name]
Integration point:  [handoff / reference]
Direction:          [A→B / B→A / Bidirectional]
Type:               [Hard handoff / Soft reference / Shared module / Sequential]
```

| Type | When | Implementation |
|------|------|----------------|
| Hard handoff | A’s boundary | `→ Load skill-b for [topic]` |
| Soft reference | A handles; B has detail | `→ See skill-b Module X` |
| Shared module | Both need same knowledge | Standalone reference; both link |
| Sequential | Always A then B | Document in both descriptions |

### Cross-skill index (current suite)

```
bc-tenancy-substantive
  → bc-tenancy-procedure    (filing / hearing)
  → bc-tenancy-advanced     (JR, human rights, strata, MHPTA)
  → bc-judicial-review-guide (BC Supreme Court)

bc-tenancy-procedure
  → bc-tenancy-substantive  (RTA citations)
  → bc-judicial-review-guide (court enforcement / JR record)

bc-tenancy-advanced (= bc-tenancy-advocacy)
  → bc-judicial-review-guide (JR mechanics)
  → bc-tenancy-substantive  (underlying RTA)

bc-judicial-review-guide
  → bc-tenancy-substantive  (RTB foundation)
  → bc-tenancy-procedure    (evidence record)

supreme-court-civil-counsel
  → all domain skills       (drafting standard + tags)

bc-notary-public            [if installed]
  → bc-tenancy-substantive
  → bc-tenancy-advanced

self-improvement
  → ALL skills              (audit, patch, synthesis)
```

---

## Module 6: Version Management

```
VERSION LOG: [skill name]
─────────────────────────
v[X.Y] — [date]
  Changed:  [what]
  Reason:   [correction / new info / gap / integration]
  Impact:   [what this fixes]
  Priority: [Critical / High / Medium / Low]
  Source:   [user / research / audit / cross-skill]
```

| Bump | Meaning |
|------|---------|
| **Major X.0** | Module rewrite or new module |
| **Minor X.Y** | Significant content addition |
| **Patch X.Y.Z** | Factual fix, small add, formatting |

When packaging: increment version · log entry · update description if triggers change · show **before/after delta**.

→ `references/version-changelog.md`

---

## Module 7: Learning Trigger Vocabulary

### Hard triggers (always run improvement protocol)

**Corrections:** that’s wrong · you missed · actually · outdated · correct section is · actual deadline is  

**Gaps:** what about… · you didn’t mention · how do I… (when skill should have covered it)  

**Requests:** improve this skill · update this skill · advance yourself · add this to your knowledge · remember this · learn from this · get better at  

### Soft triggers (scan for opportunity)

hmm · not quite · close but · user rephrases · user adds clarifying context · “I know you said X but…” · “let me explain again”

### Response

1. Acknowledge — name what’s captured  
2. Classify — gap type + priority  
3. Draft patch immediately  
4. Offer packaged skill update  

---

## Module 8: Skill Patch Format

### ADD

```
PATCH: ADD
Skill:   [skill-name]
Module:  [module # and name]
Section: [where]
Content:
  [exact text to add]
```

### REPLACE

```
PATCH: REPLACE
Skill:   [skill-name]
Module:  [module # and name]
Remove:
  [exact text]
Replace with:
  [corrected text]
Reason: [why]
```

### NEW MODULE

```
PATCH: NEW MODULE
Skill:     [skill-name]
Module #:  [next #]
Module name: [name]
Trigger:   [when used]
Content:
  [full module text]
```

### DESCRIPTION UPDATE (≤ 1024 chars)

```
PATCH: DESCRIPTION
Skill:       [skill-name]
Current:     [existing]
Updated:     [new]
Char count:  [n]
Reason:      [trigger problem solved]
```

### NEW SKILL

```
PATCH: NEW SKILL
Name:        [skill-name]
Description: [≤ 1024 chars]
Modules:     [list]
Triggers from: [skills that should reference this]
```

→ `templates/patch-*.md`

---

## Module 9: Self-Reflection Protocol

After significant conversations:

```
REFLECTION LOG
──────────────
Conversation topic:   […]
Skills activated:     […]
Skills that should have activated but didn't: […]

Performance assessment:
  Best response:      […]
  Weakest response:   […]
  Missed opportunity: […]

Knowledge delta:
  What I knew:        […]
  What was missing:   […]
  What I learned:     […]

Patches generated:    […]
Version increments:   […]

Meta-observation:     [how to improve self-improvement itself]
```

**Meta-improvement loop:** If this skill misses a correction signal → update Module 7. If patch format is insufficient → Module 8. If audit misses real gaps → Module 4. **This skill is never finished.**

→ `templates/reflection-log.md`

---

## Module 10: Advancement Roadmap

```
ADVANCEMENT ROADMAP: [skill name]
──────────────────────────────────
Current version:    [X.Y]
Last audited:       [date]
Overall score:      [X/35]

Priority patches (next session):
  P1: …
  P2: …
  P3: …

Planned expansions (next month):
  - …

Research needed:
  - …

Long-term vision (6 months):
  - …
```

**Review when:** score &lt; 25/35 · 3+ corrections in same module · law/policy changed · use case evolved · new skill needs integration  

→ `templates/advancement-roadmap.md` · `references/advancement-roadmaps.md`

---

## Reference files

| File | Purpose |
|------|---------|
| [references/gap-taxonomy.md](references/gap-taxonomy.md) | Gap types + examples |
| [references/patch-library.md](references/patch-library.md) | Archive of patches |
| [references/version-changelog.md](references/version-changelog.md) | Cross-skill changelog |
| [references/correction-log.md](references/correction-log.md) | User corrections |
| [references/advancement-roadmaps.md](references/advancement-roadmaps.md) | Active roadmaps |

## Templates

| Template | Use |
|----------|-----|
| `templates/correction-capture.md` | Correction log |
| `templates/synthesis-map.md` | Knowledge synthesis |
| `templates/audit-report.md` | Performance audit |
| `templates/patch-add.md` | ADD patch |
| `templates/patch-replace.md` | REPLACE patch |
| `templates/patch-new-module.md` | NEW MODULE |
| `templates/patch-description.md` | DESCRIPTION UPDATE |
| `templates/reflection-log.md` | Post-conversation reflection |
| `templates/advancement-roadmap.md` | Roadmap |

## Operating rules

1. Prefer **immediate patches** over “we’ll fix it later.”  
2. Never invent “learned” legal facts — synthesis must cite user/source.  
3. Critical legal corrections (deadlines, standards) → **Critical** priority + update same session if user approves install.  
4. Install patches only with user consent when writing to skill files.  
