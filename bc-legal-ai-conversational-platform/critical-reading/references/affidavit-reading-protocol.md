# Affidavit Reading Protocol

Affidavits are sworn statements. Every word is offered as evidence,
subject to rules about what can be sworn to and how.

---

## The Three-Bucket Sort

Every statement in an affidavit falls into one of three buckets:

### Bucket 1 — Personal Knowledge

Statements the affiant knows directly. Standard opening:
"I have personal knowledge of the matters deposed to except where stated
to be on information and belief."

Signals of personal knowledge:
- "I saw / heard / did / said / signed / received..."
- "On [date], I was present at..."
- "I have reviewed [documents I created or handled]..."

Weight: strongest — direct evidence.

### Bucket 2 — Information and Belief

Statements the affiant learned from someone else and believes to be true.
Must be identified as such.

Signals:
- "I am informed by X and believe..."
- "Based on information received from..."
- "I understand that..."

Weight: weaker — hearsay, but admissible in some contexts (e.g. certain
interlocutory matters).

### Bucket 3 — Argument / Opinion / Conclusion

Statements that aren't fact but characterization, argument, or legal
conclusion. Generally IMPROPER in an affidavit — should be in submissions.

Signals:
- Legal conclusions: "The landlord acted in bad faith"
- Characterizations of motive: "The tenant was being obstructive"
- Argument: "It is clear that..."
- Opinion (without qualification as expert): "This shows that..."

Weight: often strikeable. Even if not struck, courts and tribunals give
less weight to argumentative material in affidavits.

---

## The Sort in Action

Read the affidavit paragraph by paragraph and tag each statement:

```
¶ 1  "I am the landlord of the property"                       [KNOWLEDGE]
¶ 2  "I served the notice on May 1, 2024"                       [KNOWLEDGE]
¶ 3  "The tenant was being difficult about the notice"         [CHARACTERIZATION]
¶ 4  "My son needed the unit for his return from university"   [KNOWLEDGE]
¶ 5  "I understand from my property manager that..."           [INFO & BELIEF]
¶ 6  "The tenant acted in bad faith by disputing the notice"   [LEGAL CONCLUSION]
```

Result:
- ¶ 1, 2, 4: proper evidence, weight full
- ¶ 3: characterization — may be struck or discounted
- ¶ 5: information and belief — weight reduced, source should be checkable
- ¶ 6: legal conclusion — improper, should be struck or ignored

---

## The Attack Vectors

For an opposing affidavit, weaknesses cluster:

### 1. Bucket Misassignment

Argument dressed as knowledge. If the affiant says "I know that the
landlord acted in bad faith" — knowledge of a legal conclusion is not
possible; that's argument.

### 2. Missing Information Source

If a statement is information and belief but the source isn't identified,
the statement can't be weighed. Move to strike or discount.

### 3. Contradiction With Documents

If the affiant says "I did X" but a document produced in the same
proceeding shows they did Y, the affidavit's credibility is impeached.

### 4. Internal Inconsistency

If ¶ 5 contradicts ¶ 20, the credibility of both suffers.

### 5. Selective Presentation

If the affiant states "I did X" but omits that they also did Y, and Y
would put X in context, the affidavit is selectively presented. This is
attack surface on cross-examination.

### 6. Improper Argument

Every legal conclusion, characterization, or argument in the affidavit is
a candidate for a motion to strike or, at minimum, for arguing that
weight should be reduced.

---

## The Verification Sweep

For every factual claim in the affidavit:

```
CLAIM                       │ VERIFIABLE?        │ VERIFIED?
────────────────────────────┼────────────────────┼──────────
[claim]                     │ [documents / other │ [Y/N]
                            │  witnesses / etc]  │
```

Verifiable claims that check out — accept as strong evidence.
Verifiable claims that fail verification — attack surface.
Unverifiable claims — weight depends on credibility of the affiant.

---

## Cross-Examination Preparation

If cross-examination is available, use the affidavit as your cross
outline:

```
¶ N  [statement]  →  Cross question: [what you'd ask]
                     Purpose: [impeach / clarify / expand / lock in]
                     Documents: [what to have ready]
```

Every load-bearing statement in the affidavit should have a cross
question — even if you decide not to ask it. The list of questions IS
your preparation.

---

## Your Own Affidavit — Same Rules Applied

When drafting your own affidavit, run the same sort BEFORE swearing:

```
□ Every statement is bucket-1 (knowledge) or clearly bucket-2 (I&B)
□ No bucket-3 (argument, conclusion, characterization) in the affidavit
□ Every I&B statement identifies its source
□ Every fact is verifiable if challenged
□ No selective presentation — full context provided where relevant
□ No internal inconsistency
□ Every statement is capable of being sworn honestly
```

Argument goes in submissions. Evidence goes in affidavits. Keep them
separate — the affidavit is stronger for it.
