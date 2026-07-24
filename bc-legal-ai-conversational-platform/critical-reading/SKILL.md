---
name: critical-reading
description: >
  Skill for decomposing complex source documents — court decisions, academic
  papers, opposing affidavits, technical specifications, statutes, expert
  reports, contracts. Covers structural analysis (what kind of document is
  this, what work is each section doing), argument extraction (what is the
  author actually claiming and why), evidence-vs-assertion sorting, hidden
  assumption surfacing, weakness identification, and productive marginalia.
  ALWAYS trigger when: user uploads or references a court decision, RTB
  decision, opposing submission, affidavit, academic paper, technical spec,
  contract, statute section, expert report, or any dense document they need
  to understand or respond to; user asks to "break down", "analyze", "pull
  apart", "find the holes in", or "understand" a document. Pairs with
  supreme-court-litigation-counsel (for legal analysis), argument-architecture
  (for identifying opposing argument structure), canlii-boa-builder (for
  reading cases before citing them), and cognitive-awareness (for
  calibrating confidence in interpretive claims).
---

# Critical Reading Skill

Slow reading, structured.

Most documents you'll encounter — court decisions, opposing affidavits,
academic papers, contracts — reward decomposition. Read once fast to get
the shape. Read again slowly, with a structure. This skill is that structure.

---

## Skill Tree

| Module | Domain |
|---|---|
| 1 | Document Type Recognition — what you're actually reading |
| 2 | Structural Decomposition — what work each section does |
| 3 | Argument Extraction — what the author claims and why |
| 4 | Evidence vs Assertion Sorting |
| 5 | Hidden Assumption Surfacing |
| 6 | Weakness Identification |
| 7 | Cross-Reference Mapping |
| 8 | Productive Marginalia — what to write in the margins |
| 9 | Reading for Response — what you'll need to answer |
| 10 | The Second Read |

---

## Module 1: Document Type Recognition

Before you can read a document well, you need to know what kind of
document it is. Different types do different work.

### The Document Type Taxonomy

```
LEGAL DOCUMENTS
  Court decisions       — reasoning applied to facts, binding force varies
  Tribunal decisions    — same, lower binding force
  Affidavits            — sworn statements of fact
  Petitions/factums     — argumentative pleadings
  Statutes              — enacted rules
  Regulations           — subordinate rules
  Contracts             — negotiated obligations
  Expert reports        — opinion evidence with methodology
  Legal memos           — internal analysis, not binding

ACADEMIC DOCUMENTS
  Peer-reviewed papers  — claims with methodology and evidence
  Preprints             — same, without peer review filter
  Theses                — extended arguments with literature review
  Books                 — extended treatments
  Textbooks             — synthesized state of a field
  Reviews / surveys     — meta-treatments of a literature
  Conference papers     — shorter, sometimes higher-velocity

TECHNICAL DOCUMENTS
  Specifications        — normative descriptions of a system
  RFCs                  — standards proposals
  API docs              — reference material
  Design documents      — proposals with rationale
  Post-mortems          — retrospective analysis
  Whitepapers           — hybrid academic/marketing
```

Each type has a different reading protocol. A court decision is read
differently from an affidavit which is read differently from a spec.

### Type-Specific Notes

- **Court decisions** — separate reasoning (ratio) from asides (obiter);
  identify the standard of review, the test applied, and the specific
  findings; note dissents if any
- **Affidavits** — everything is sworn; distinguish knowledge (personal),
  information & belief (secondhand), and argumentative statements
  (usually improper)
- **Academic papers** — separate the CONTRIBUTION from the CONTEXT;
  most papers are 80% context; the load-bearing claim usually fits in 1-2
  paragraphs
- **Specs** — identify normative language (MUST, SHOULD, MAY per RFC 2119
  convention); note ambiguities

---

## Module 2: Structural Decomposition

Every document has structure. Some documents make it explicit (headings,
numbered sections). Some hide it (long affidavits, dense academic prose).
Extract the structure either way.

### The Section-Purpose Table

For any substantial document:

```
SECTION | PURPOSE                | LOAD-BEARING?
────────┼────────────────────────┼──────────────
[1]     | [what this section does] | [Y/N]
[2]     | [what this section does] | [Y/N]
[3]     | [what this section does] | [Y/N]
...
```

Load-bearing sections carry the argument. Non-load-bearing sections
frame it, provide background, or fill space.

### Load-Bearing Section Signals

Load-bearing sections usually:
- Introduce a novel claim
- Apply a rule to specific facts
- Present evidence that supports a conclusion
- State a holding
- Draw a distinction the rest of the document depends on

Non-load-bearing sections usually:
- Restate what's already been said
- Provide historical or general context
- Handle procedural or administrative matters
- Acknowledge counterarguments only to dismiss them briefly

Time spent decoding non-load-bearing sections is time not spent on the
sections that matter. Speed-read the framing, slow-read the load.

---

## Module 3: Argument Extraction

For any document making a claim, extract:

```
CLAIM:      [what the author is arguing]
GROUNDS:    [what evidence they provide]
WARRANT:    [the reasoning link they rely on]
AUTHORITY:  [what they cite as support]
LIMITATIONS:[what they concede or acknowledge as bounded]
```

This is Toulmin structure applied backward — reverse-engineering the
argument.

### For Court Decisions Specifically

```
STANDARD OF REVIEW: [what standard the court applied]
ISSUE:              [what question the court asked]
TEST:               [what test the court used to answer it]
FINDINGS:           [what the court found on the facts]
HOLDING:            [the court's answer]
REASONING:          [the ratio — how the court got from findings to holding]
OBITER:             [any asides that aren't part of the ratio]
```

The distinction between ratio and obiter matters enormously for legal
work. Only ratio has binding force. Obiter is persuasive at best. Extract
them separately.

---

## Module 4: Evidence vs Assertion Sorting

A document mixes evidence (things offered as facts) with assertions
(things claimed but not established).

### The Sort

```
EVIDENCE                        │  ASSERTION
────────────────────────────────┼────────────────────────────────
Sworn statements of personal    │  Conclusory statements of law
  knowledge                     │
Documents produced              │  Characterizations of motive
Photographs, records            │  Predictions
Expert opinions (with method)   │  Interpretations
Admitted facts                  │  Argumentative descriptions
Cited authorities               │  Uncited claims
```

Both are legitimate in different roles. Evidence establishes fact.
Assertion draws conclusions from evidence.

The failure mode is when a document presents assertion AS evidence, or
treats evidence AS if it directly supported a stronger conclusion than it
does.

### The Assertion-Dressed-as-Evidence Check

For any claim in the document that looks factual, ask:
- Is this actually a fact, or is it a conclusion drawn from facts?
- Is the underlying fact provided or assumed?
- Would a neutral reader see the same evidence and reach the same
  conclusion?

If no, it's assertion, not evidence. Mark it as such in your reading.

---

## Module 5: Hidden Assumption Surfacing

Every argument rests on premises. Some are stated. Some are hidden —
not because the author is trying to hide them, but because they seem so
obvious to the author that they don't need stating.

Hidden assumptions are where opposing arguments often live.

### The Hidden Assumption Scan

For each load-bearing claim in the document, ask:

```
□ What must be true for this claim to hold?
□ Which of those things has the author stated?
□ Which has the author assumed?
□ Are the assumed things actually true?
□ Would the argument still hold if any of them were false?
```

The last question is the most powerful. A hidden assumption whose falsity
would collapse the argument is a load-bearing hidden assumption. Those are
worth attacking or defending, depending on your role.

### Example — RTB Decision

An RTB decision might state:
"The landlord served the notice in good faith."

Hidden assumptions embedded in that claim:
- "Good faith" here is legal-technical, not colloquial
- The evidence supporting the good-faith finding is sufficient under the
  applicable test
- The applicable test is Gichuru (or its successors)
- The evidence was properly weighed

Attack any of these and you attack the finding.

---

## Module 6: Weakness Identification

Once the argument is extracted (Module 3) and assumptions are surfaced
(Module 5), scan for structural weaknesses.

### The Weakness Catalog

```
□ MISSING PREMISE — argument requires X but X is never established
□ WEAK PREMISE — X is established but only barely
□ FALLACY — argument commits a formal or informal fallacy
□ SCOPE OVERREACH — conclusion exceeds what premises support
□ AUTHORITY MISUSE — cited authority doesn't say what's claimed
□ EVIDENCE MISWEIGHT — evidence supports a weaker conclusion
□ UNADDRESSED COUNTER — obvious counter-argument goes unaddressed
□ INTERNAL INCONSISTENCY — document contradicts itself
□ FACT-LAW GAP — legal test not fully mapped to facts
□ TEST OMISSION — legal test not correctly stated
```

For an opposing document, weaknesses are attack surface. For your own
document (or a friendly one), weaknesses are things to fix.

### Weakness Prioritization

Not every weakness is worth exploiting or fixing.

- **Load-bearing weaknesses** — if this weakness holds, the whole
  argument fails. Highest priority.
- **Contributory weaknesses** — if this weakness holds, the argument is
  weaker but not defeated. Medium priority.
- **Cosmetic weaknesses** — minor flaws that don't affect the argument.
  Low priority; often not worth raising.

Focus on load-bearing weaknesses. Raising cosmetic weaknesses in an
opposing document wastes your credibility. Fixing them in your own
document wastes your time.

---

## Module 7: Cross-Reference Mapping

Complex documents reference other documents. Track those references.

### The Cross-Reference Log

```
REFERENCE                    │ ROLE                    │ HAVE READ?
─────────────────────────────┼─────────────────────────┼───────────
[Case cite]                  │ Cited for [purpose]     │ [Y/N]
[Statute section]            │ Applied for [purpose]   │ [Y/N]
[Prior filing]               │ Referenced re [purpose] │ [Y/N]
[Expert report]              │ Basis for [finding]     │ [Y/N]
```

### Discipline

- Any cited case that's load-bearing should be read, not just noted
- Any statute section referenced should be pulled and checked
- Any prior filing referenced should be located and read
- Cited authorities that don't actually say what they're cited for are a
  weakness (Module 6)

The document is the tip of an iceberg. The cited authorities and prior
filings are what's underwater. Skip them and you're reading with your
eyes half-closed.

---

## Module 8: Productive Marginalia

What to write in the margins as you read.

### The Marginalia Vocabulary

Use consistent symbols so your second read is faster.

```
!!!    Strong point (positive) or serious weakness (negative)
??     I don't understand this yet
✓      Verified against source
✗      Contradicted by source
→      Cross-reference to another section
◆      Load-bearing claim
▲      Assumption I need to check
♦      Counter-argument I need to develop
∴      Conclusion
∵      Because — reasoning move
Δ      Change from prior position
[N]    Note-to-self, expanded on separate page
```

### Marginalia Discipline

- Mark as you read, not after
- Prefer symbols to words — faster on second read
- If something confuses you (??), mark it and keep reading; come back
- If something seems load-bearing (◆), mark it before deciding what to
  do about it
- If you notice a counter-argument (♦), mark it — even if you can't
  articulate it yet

The marginalia becomes a map of the document that you can navigate on
the second read.

---

## Module 9: Reading for Response

If you're going to respond to the document — with a factum, a reply, a
review, a rebuttal — read with the response in mind.

### The Response-Ready Extraction

```
POINTS YOU MUST ADDRESS
  1. [Point] — [document location] — [priority]
  2. [Point] — [document location] — [priority]
  3. [Point] — [document location] — [priority]

POINTS YOU COULD ADDRESS
  1. [Point] — [why it's optional]
  2. [Point] — [why it's optional]

POINTS YOU SHOULD NOT ADDRESS
  1. [Point] — [why raising it hurts you]
  2. [Point] — [why raising it hurts you]

WEAKNESSES TO EXPLOIT
  1. [Weakness] — [document location] — [how to use it]
  2. [Weakness] — [document location] — [how to use it]

ADMISSIONS TO PRESERVE
  1. [Statement] — [document location] — [why useful]
  2. [Statement] — [document location] — [why useful]
```

The last category is often overlooked. Documents you're responding to
sometimes admit things useful to you. Extract them.

---

## Module 10: The Second Read

Most documents worth analyzing deserve two reads. The first read gets
the shape. The second read fills in the analysis.

### First Read

- Get the document type (Module 1)
- Get the structure (Module 2)
- Get the main argument (Module 3)
- Mark up with marginalia (Module 8)
- Speed: fast

### Second Read

- Extract argument formally (Module 3)
- Sort evidence from assertion (Module 4)
- Surface hidden assumptions (Module 5)
- Identify weaknesses (Module 6)
- Log cross-references (Module 7)
- If responding, build response-ready extraction (Module 9)
- Speed: slow, deliberate

### When One Read Is Enough

- Documents you've read before and are re-orienting to
- Short documents where the shape and the load are the same
- Documents you're reading for gist, not for analysis or response

### When Three Reads Are Warranted

- The document is opposing counsel's factum you must respond to
- The document is a court decision you're appealing or applying
- The document is a foundational academic paper you're extending
- The document has hidden depth (dense specs, complex contracts, layered
  legal reasoning)

Match the number of reads to the stakes.

---

## Reference Files

- `references/court-decision-reading-protocol.md` — full protocol for judicial decisions
- `references/affidavit-reading-protocol.md` — full protocol for sworn statements
- `references/academic-paper-reading-protocol.md` — full protocol for papers
- `references/contract-reading-protocol.md` — full protocol for contracts

## Templates

- `templates/section-purpose-table.md` — blank structural decomposition
- `templates/argument-extraction.md` — blank argument extraction
- `templates/weakness-log.md` — blank weakness identification
- `templates/response-ready-extraction.md` — blank response-preparation

---

## Integration Points

- `argument-architecture` → reverse-engineers arguments this skill extracts
- `supreme-court-litigation-counsel` → uses critical-reading for opposing submissions
- `canlii-boa-builder` → uses critical-reading for authority verification
- `bc-judicial-review-guide` → uses critical-reading on RTB decisions being reviewed
- `owings-sanghera-jr-strategy` → uses critical-reading on the impugned decisions
- `cognitive-awareness` → applies Module 2 (epistemic calibration) to interpretive claims
