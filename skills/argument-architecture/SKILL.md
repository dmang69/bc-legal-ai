---
name: argument-architecture
description: >
  Structured argumentation skill — building rigorous arguments for legal
  submissions, thesis chapters, technical proposals, and anything requiring
  a defensible reasoning chain. Covers IRAC and IRAC++ for legal writing,
  the Toulmin model for general argumentation, deductive/inductive/abductive
  chain construction, syllogistic form, argument mapping, counter-argument
  anticipation, and the anatomy of a "why should the reader believe you"
  paragraph. ALWAYS trigger when: user asks to draft a submission, factum,
  petition, thesis section, position paper, technical proposal, or any
  document requiring persuasion; user says "argue that", "make the case
  for", "structure this argument", "how do I frame"; or when reviewing an
  existing argument for logical gaps. Pairs with supreme-court-litigation-counsel,
  canlii-boa-builder, and bc-judicial-review-guide for legal work; pairs
  with cognitive-awareness for reasoning-quality checks.
---

# Argument Architecture Skill

Every serious argument has bones. This skill is those bones.

Used for legal submissions, thesis chapters, technical proposals — anything
where the reader must be moved from disagreement or neutrality to agreement
through structured reasoning.

---

## Skill Tree

| Module | Domain |
|---|---|
| 1 | IRAC++ — the legal argument spine |
| 2 | Toulmin Model — general argumentation structure |
| 3 | Deductive / Inductive / Abductive chains |
| 4 | Syllogistic form and its traps |
| 5 | Argument mapping — visualizing structure before drafting |
| 6 | Counter-argument anticipation |
| 7 | The Persuasion Paragraph — micro-structure |
| 8 | Logical fallacy audit |
| 9 | Bridge sentences — the connective tissue |
| 10 | Argument QA — testing before submission |

---

## Module 1: IRAC++

Classical IRAC (Issue, Rule, Application, Conclusion) is the legal spine.
IRAC++ adds two elements that separate competent submissions from strong ones.

```
I — ISSUE          What is the precise question?
R — RULE           What is the governing law?
   R+ — SUB-RULE   What sub-rules, tests, or standards apply?
   R++ — AUTHORITY What case, statute, or regulation establishes each?
A — APPLICATION    How do the facts meet or fail each element?
   A+ — COUNTER    What is the strongest opposing application?
C — CONCLUSION     The answer, restated with force
```

### The Issue Statement Test

An issue statement fails if any of the following is true:
- It's a topic, not a question
- It's a yes/no question when the real issue is a "how" or "to what extent"
- It buries multiple sub-issues under one label
- It uses conclusory language ("whether the landlord acted in bad faith" —
  presumes the framing; better: "whether s.51 permits the use asserted")

### The Rule Statement Test

A rule statement fails if:
- It paraphrases without citation
- It cites without quoting the operative words
- It omits the test the court will actually apply
- It states the rule without stating its exceptions

### The Application Test

An application fails if:
- It restates facts without connecting them to rule elements
- It skips an element
- It doesn't address the counter-application

---

## Module 2: Toulmin Model

For non-legal argumentation (thesis chapters, technical proposals), Toulmin
is the general-purpose structure.

```
CLAIM       What you're arguing
GROUNDS     Evidence supporting the claim
WARRANT     The reasoning link connecting grounds to claim
BACKING     Support for the warrant itself
QUALIFIER   Under what conditions the claim holds
REBUTTAL    Where the claim would fail
```

### Why Toulmin Beats "Claim + Evidence"

Naive argument: "X, because Y."
Toulmin: "X (claim), because Y (grounds), and Y implies X because Z (warrant),
which we know from W (backing), except when V is present (rebuttal)."

The naive version hides the warrant. The Toulmin version exposes it — and
exposed warrants can be tested, defended, or corrected.

Most argument failures happen at the warrant, not the grounds. Toulmin
forces the warrant into view.

---

## Module 3: Deductive / Inductive / Abductive Chains

Every argument runs on one of three engines. Know which you're using.

### Deductive

Structure: If premises are true, conclusion MUST be true.
Use when: legal rule application, mathematical proof, logical derivation.
Failure mode: false premise, invalid inference form.

Example:
```
P1: A landlord ending tenancy under s.51 must occupy in good faith
P2: This landlord's affidavits show no intention to occupy
C:  Therefore this s.51 notice is invalid
```

### Inductive

Structure: If premises are true, conclusion is PROBABLY true.
Use when: pattern arguments, empirical claims, evidence-weight arguments.
Failure mode: unrepresentative sample, hidden variables.

Example:
```
P1: In cases A, B, C, D, and E, this arbitrator ruled against tenants
P2: These cases had features similar to the present case
C:  This arbitrator is likely to rule against the tenant here (probabilistic)
```

### Abductive

Structure: The best explanation for the evidence is X.
Use when: motive arguments, bad-faith allegations, inferring intent.
Failure mode: assuming one explanation without ruling out others.

Example:
```
Evidence: Landlord served s.49, moved in for 6 weeks, re-rented at higher rent
Best explanation: The stated intention was pretextual (i.e. bad faith)
```

Always name which engine you're using when the reader might mistake one
for another. Abductive arguments dressed as deductive ones fail hard on
appeal.

---

## Module 4: Syllogistic Form and Its Traps

The syllogism is the atom of deductive argument. Get the form right or
the argument fails on inspection.

### Valid Form

```
Major:  All A are B
Minor:  This is an A
Concl:  Therefore this is a B
```

### Common Traps

**Affirming the consequent (INVALID):**
```
If A then B
B is true
Therefore A                ← WRONG. Many things could cause B.
```

**Denying the antecedent (INVALID):**
```
If A then B
A is false
Therefore B is false        ← WRONG. B could hold for other reasons.
```

**Undistributed middle (INVALID):**
```
Some A are B
This is a B
Therefore this is an A     ← WRONG. Some B are not A.
```

Before submitting any argument that uses "therefore", check that it's
one of the valid forms — modus ponens, modus tollens, or hypothetical
syllogism. Anything else, restructure.

---

## Module 5: Argument Mapping

Before drafting, map. Drafting-first produces meandering arguments.
Mapping-first produces tight ones.

### The Map Structure

```
                    [MAIN CLAIM]
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   [Sub-claim 1]    [Sub-claim 2]    [Sub-claim 3]
        │                │                │
    ┌───┴───┐        ┌───┴───┐        ┌───┴───┐
  [Evid] [Evid]    [Evid] [Evid]    [Evid] [Evid]
```

### Mapping Discipline

- Each sub-claim must independently support the main claim
- If two sub-claims collapse into each other, merge them
- If a sub-claim has no independent evidence, it's a restatement, cut it
- If evidence supports multiple sub-claims, note the cross-support
- Counter-arguments get their own branch, with responses attached

The map is not the document. It's the skeleton. The document adds the
flesh — transitions, tone, specifics — but the skeleton stays intact.

---

## Module 6: Counter-Argument Anticipation

An argument that doesn't address counter-arguments is half an argument.
A judge, reviewer, or reader will supply the counter-argument themselves —
and if you haven't addressed it, they'll assume you can't.

### The Counter-Argument Protocol

For every load-bearing claim, ask:

1. What is the strongest possible objection?
2. Who would make it?
3. On what basis?
4. What is the best response?

Then, in the draft, address the counter-argument BEFORE the reader raises it
in their head. Signals: "It might be argued that... but this fails because..."

### Concession Discipline

Sometimes the honest response to a counter-argument is partial concession.
This is a strength move, not a weakness move — provided you show why the
conceded point doesn't defeat your claim.

Bad concession: "The other side has a point about X."
Good concession: "The strongest form of the objection is X. That objection
would defeat this claim if [condition]. However, [condition] does not hold
here because [reasons]."

---

## Module 7: The Persuasion Paragraph

Micro-structure — the paragraph as unit of persuasion.

```
1. TOPIC SENTENCE         The claim in one line
2. RULE / PRINCIPLE       What governs this
3. AUTHORITY              Where it comes from
4. APPLICATION            Facts meeting the rule
5. INFERENCE              What this proves
6. TRANSITION             Handoff to the next paragraph
```

Every persuasion paragraph should be able to survive isolation. If you
extracted it from the document and read it standalone, the reader should
still understand what claim it's making and why.

### The Wince Test

Read each paragraph. If you wince at any sentence — because it's vague,
overclaimed, unsupported, or padding — cut or rewrite it. Winces are
signals from your own trained instinct. Don't override them.

---

## Module 8: Logical Fallacy Audit

Before submitting any argument, scan for these common fallacies.

### The Fallacy Sweep

```
□ Ad hominem — attacking the arguer, not the argument
□ Straw man — misrepresenting the opposing position to make it easier to attack
□ Slippery slope — asserting a chain of consequences without warrant
□ Appeal to authority — citing authority where the authority isn't relevant
□ Appeal to popularity — because many believe X, X is true
□ Circular reasoning — using the conclusion as a premise
□ False dilemma — presenting two options when more exist
□ Hasty generalization — sweeping claim from limited examples
□ Post hoc — because B followed A, A caused B
□ Equivocation — using one word in two different senses in the same argument
□ Red herring — introducing an irrelevant point to distract
□ Tu quoque — deflecting a criticism by pointing at the critic
```

Each of these has a legitimate cousin. Citing authority is fine when the
authority IS relevant. Pointing out inconsistency is fine when consistency
IS at issue. The fallacy is the misapplication, not the form.

---

## Module 9: Bridge Sentences

The connective tissue between arguments. Weak bridges make strong arguments
read like disconnected paragraphs.

### Bridge Patterns

| Pattern | Use |
|---|---|
| "This establishes X. It follows that..." | Deductive continuation |
| "The same principle applies to..." | Extension |
| "By contrast, ..." | Distinction |
| "This is not the only ground. Additionally..." | Cumulative |
| "Even if X were not established, Y independently..." | Alternative |
| "The strongest response is..." | Anticipating objection |
| "Turning to the second issue..." | Section handoff |

Bridges should NAME the logical relationship. "Also" hides the relationship.
"By contrast" reveals it.

---

## Module 10: Argument QA

Final gate before submission. Applies to legal filings, thesis chapters,
technical proposals — anything argumentative.

### The QA Checklist

```
□ Every claim is either evident, cited, or reasoned to
□ Every citation actually says what it's cited for
□ Every deductive chain has valid form
□ Every inductive chain acknowledges its probabilistic nature
□ Every abductive chain acknowledges alternative explanations
□ Every load-bearing counter-argument is addressed
□ Every paragraph passes the wince test
□ Every fallacy in Module 8 has been scanned for
□ Every bridge sentence names the relationship
□ Every conclusion follows from its premises
□ The main claim from the intro matches the main claim in the conclusion
```

### The Hostile Reader Simulation

Read the argument as if the reader is:
- Intelligent
- Skeptical of your position
- Reading fast
- Looking for a reason to disagree

If they'd find one, so will the actual reader. Fix it.

---

## Reference Files

- `references/irac-worked-examples.md` — IRAC++ applied to real fact patterns
- `references/toulmin-worked-examples.md` — Toulmin applied to non-legal arguments
- `references/fallacy-catalog.md` — expanded fallacy list with examples and antidotes
- `references/argument-templates.md` — skeleton structures for common argument types

## Templates

- `templates/irac-blank.md` — blank IRAC++ template
- `templates/toulmin-blank.md` — blank Toulmin template
- `templates/argument-map.md` — blank argument map
- `templates/counter-argument-log.md` — counter-argument tracker
- `templates/qa-checklist.md` — final QA sweep

---

## Integration Points

- `supreme-court-litigation-counsel` → uses this skill's Module 1 (IRAC++) for factum drafting
- `canlii-boa-builder` → uses this skill's Module 6 (counter-argument) for identifying cases the other side will cite
- `bc-judicial-review-guide` → uses this skill's Module 1 for grounds structuring
- `cognitive-awareness` → runs Module 10 (Argument QA) as an extension of its pre-send checklist
- `self-improvement` → captures failed arguments as patches
