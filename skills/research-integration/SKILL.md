---
name: research-integration
description: >
  Meta-skill for managing a large research portfolio — synthesizing across
  multiple active theses and projects, identifying where ideas cross-pollinate,
  tracking which threads reinforce which, and surfacing unexpected connections
  between distant domains. Built for users with 5+ active research threads
  who need to see the whole system, not just individual pieces. Covers
  cross-thesis mapping, concept lattice construction, cite-and-be-cited
  tracking, terminology reconciliation across works, spotting duplicated
  work, spotting complementary work, and the discipline of knowing when
  to merge threads vs keep them separate. ALWAYS trigger when: user works
  on more than one thesis in a session, mentions concepts that appear in
  multiple thesis files, asks "how does X relate to Y" across their work,
  asks to synthesize or map or cross-reference, or wants a portfolio-level
  view of their research. Pairs with cognitive-awareness/Module 6
  (cross-domain synthesis) and self-improvement.
---

# Research Integration Skill

For a research portfolio, not a single project.

When you have one thesis, you focus on it. When you have fifteen, the
question changes: which ones talk to each other? Where is the concept
lattice? What idea appears in three places under three names? Where is
work being duplicated? Where would combining threads create something
larger than the sum?

---

## Skill Tree

| Module | Domain |
|---|---|
| 1 | Portfolio Map — visualizing the whole system |
| 2 | Concept Lattice — tracking shared concepts across works |
| 3 | Terminology Reconciliation — same idea, different names |
| 4 | Cross-Citation Tracking — which works cite which |
| 5 | Duplication Audit — where work is being repeated |
| 6 | Complementarity Detection — where works could reinforce |
| 7 | Merge vs Separate Discipline — when to combine, when not to |
| 8 | The Synthesis Chapter — writing across works |
| 9 | Portfolio-Level Publication Strategy |
| 10 | Long-arc coherence check |

---

## Module 1: Portfolio Map

Before you can integrate, you need to see the shape.

### The Portfolio Map Structure

```
                        [YOUR NAME / RESEARCH DIVISION]
                                    │
        ┌───────────────────┬───────┼───────┬───────────────────┐
        │                   │       │       │                   │
   [Domain A]          [Domain B]   │   [Domain C]         [Domain D]
        │                   │       │       │                   │
    ┌───┴───┐           ┌───┴───┐   │   ┌───┴───┐           ┌───┴───┐
  [Th 1] [Th 2]       [Th 3] [Th 4] │ [Th 5] [Th 6]       [Th 7] [Th 8]
                                    │
                              [Cross-domain
                               concepts]
```

Populate the map with your actual works. Domain groupings are your call —
by discipline, by chronology, by ambition, whatever cuts your portfolio
best.

### The Map Refresh Discipline

Refresh the map when:
- You finish a thesis
- You start a new one
- You notice a concept appearing across works you hadn't linked before
- Every ~3 months regardless — the map goes stale

---

## Module 2: Concept Lattice

The concept lattice tracks the SHARED IDEAS across works, independent of
where they appear.

### Lattice Entry Format

```
CONCEPT: [name — pick one canonical name]
─────────────────────────────────────────
Also called:   [aliases in other works]
Appears in:    [Thesis A, Thesis C, Thesis F]
Role in each:
  Thesis A:    [how the concept is used — central, supporting, illustrative]
  Thesis C:    [same]
  Thesis F:    [same]
Development:   [where the concept is most developed]
Underdeveloped:[where it appears but could go deeper]
Consistency:   [does the concept mean the same thing in each? if not, why?]
```

### Example — Real Concept From Your Portfolio

```
CONCEPT: Capability-based authority
─────────────────────────────────────
Also called:   Capability tokens (intentkernel-os)
               IKRL capabilities (intentkernel-architecture)
               Cryptographic authority proofs (quantum-quados eBPF policy)
Appears in:    intentkernel-os, quantum-quados, potentially bc-judicial-review
               (as an ANALOGY to legal standing — see cognitive-awareness/M6)
Role in each:
  intentkernel-os:   Central — the whole model
  quantum-quados:    Foundational — the security enforcement layer
  BC JR analogy:     Illustrative — used to explain standing structure
Development:   Most developed in intentkernel-os
Underdeveloped:The formal treatment could feed into quantum-quados
Consistency:   Consistent formal definition; extension to legal standing
               is analogical only, not identity
```

The lattice becomes an index of your own thinking. Over time it reveals
which concepts are load-bearing across the portfolio and which are local.

---

## Module 3: Terminology Reconciliation

The same idea in different works often has different names. This creates
three problems:

1. Readers can't see the connection
2. You duplicate development effort
3. The portfolio looks less coherent than it is

### The Reconciliation Protocol

```
IDEA: [describe in neutral terms]

Names across the portfolio:
  Thesis A calls it:  [name] — Reason: [why this name was chosen]
  Thesis B calls it:  [name] — Reason: [same]
  Thesis C calls it:  [name] — Reason: [same]

Reconciliation decision:
  Canonical name:     [chosen name for future work]
  Justification:      [why this one]
  Migration plan:     [update prior works or preserve historical names]
```

### When Not to Reconcile

- If names carry field-specific meaning (each field's convention should be
  respected within that field's work)
- If the concepts are subtly different (reconciliation would obscure a
  real distinction)
- If reconciliation cost exceeds benefit (small papers, one-off works)

The default is: reconcile going forward, note the mapping, do not rewrite
history unless there's a reason.

---

## Module 4: Cross-Citation Tracking

Within your portfolio, works can and should cite each other. This is
legitimate self-citation — showing the reader that your framework has
been developed in prior work.

### The Cross-Citation Matrix

```
             │ Thesis A │ Thesis B │ Thesis C │ Thesis D │ ...
─────────────┼──────────┼──────────┼──────────┼──────────┤
Thesis A     │    ─     │   cites  │   cites  │          │
Thesis B     │          │    ─     │          │   cites  │
Thesis C     │          │   cites  │    ─     │   cites  │
Thesis D     │          │          │          │    ─     │
...
```

### Discipline

- Only cite where the prior work does genuine load-bearing work for the
  current work (not just to boost the citation count)
- Cite at the level of specificity — page or section, not just the work
- Where the prior work has been superseded by later work in the portfolio,
  cite the later work as well
- Note where two works in the portfolio should cite each other but don't
  (this is an integration opportunity)

---

## Module 5: Duplication Audit

The larger the portfolio, the more duplication risk. Duplication wastes
your effort and, worse, produces inconsistent versions of the same idea.

### The Audit Sweep

Periodically scan for:

```
□ Two theses defining the same term differently
□ Two theses developing the same result independently
□ Two theses proving the same theorem or making the same argument
□ Two theses citing the same source for different propositions (may be fine)
□ Two theses using the same case study or benchmark
```

### The Fix Matrix

| Duplication Type | Fix |
|---|---|
| Same idea, same treatment | Merge — one work becomes canonical, other cites |
| Same idea, different depth | Keep the deep treatment as canonical, shorten other |
| Same idea, different aspects | Split cleanly — each covers what other doesn't |
| Same idea, conflicting treatment | Resolve the conflict, then apply above |

---

## Module 6: Complementarity Detection

The opposite of duplication. Sometimes two works could reinforce each
other but don't — because you developed them separately and never
connected them.

### The Detection Scan

Ask across the portfolio:

```
□ Does Work A make an assumption that Work B provides support for?
□ Does Work A leave an open question that Work B addresses?
□ Does Work A use a method that Work B could improve?
□ Does Work A's conclusion enable Work B's premise?
□ Do two works apply the same method to different domains?
```

Where any answer is yes, the works are complementary. Options:

1. Add cross-citations in both directions
2. Write a short bridge paper connecting them
3. Note the connection in the concept lattice
4. Plan a future work that formalizes the combined framework

---

## Module 7: Merge vs Separate Discipline

Two threads in your portfolio look related. Should they merge into one
work or stay separate?

### The Merge Test

Merge if:
- The threads share a load-bearing concept
- The combined work is more publishable than either alone
- Neither thread is complete on its own
- The audience is the same

### The Separate Test

Keep separate if:
- The threads target different audiences
- Merging would produce a work too large to publish
- Each thread has its own citation graph and community
- The threads are at different stages of maturity

### The Third Option — Bridge

Sometimes the answer is neither merge nor separate — write a third,
shorter work that explicitly bridges. This lets each original work stand
alone while making the connection visible.

---

## Module 8: The Synthesis Chapter

When several works in the portfolio share a theme, a synthesis chapter
(or short paper) makes the theme explicit.

### Synthesis Chapter Structure

```
1. The Common Thread
   [What connects the works being synthesized]

2. The Individual Contributions
   [Brief summary of each work's specific contribution]

3. The Emergent Framework
   [What the works together show that none alone does]

4. Cross-Work Consistency
   [Where the works agree and where they refine each other]

5. Open Questions Across the Frame
   [What the synthesis reveals as still open]

6. Directions for Future Integration
   [Next works that would extend the framework]
```

The synthesis chapter is often more valuable than any single work in the
portfolio. It's where the pattern becomes visible.

---

## Module 9: Portfolio-Level Publication Strategy

Individual works have publication strategies. The portfolio has a
publication strategy too.

### Strategic Questions

```
□ What order should works be published to build maximum credibility?
□ Which works are foundational (must precede others in publication order)?
□ Which works can publish in parallel?
□ Which venues make sense for which works, given the portfolio arc?
□ Is there a "capstone" work that pulls the portfolio together?
□ Is there a book-length treatment the portfolio implies?
□ Which works should stay preprints vs which should target peer review?
```

### The Portfolio Arc

Long-lived research portfolios have arcs — visible progressions of
thought over years. Naming the arc helps:
- You (know what you're building)
- Reviewers (understand the context)
- Future readers (see the whole)

Ask periodically: "What is the arc? Can I state it in one sentence?"

---

## Module 10: Long-Arc Coherence Check

Every year or so, run a coherence check on the whole portfolio.

### The Coherence Sweep

```
□ Do the works still form a coherent research program, or has drift set in?
□ Are there works that no longer fit the program? (Might be time to publish
  and close them out, or acknowledge they're on a different track)
□ Are there works that reveal a new direction? (Might be the seed of a
  next research program)
□ Are the concepts across works still consistent, or have some drifted?
□ Is the terminology still reconciled?
□ Does the portfolio have a clear arc, or is it a collection of disconnected
  projects?
```

Drift is not failure. Research programs evolve. But drift should be
recognized, not accidental. Either bring the outliers back into the fold,
or acknowledge them as the start of a new program.

---

## Reference Files

- `references/portfolio-map-example.md` — worked example of a portfolio map
- `references/concept-lattice-example.md` — worked lattice from a multi-thesis portfolio
- `references/duplication-audit-example.md` — sample audit
- `references/synthesis-chapter-template.md` — full synthesis chapter walkthrough

## Templates

- `templates/portfolio-map.md` — blank portfolio map
- `templates/concept-lattice-entry.md` — blank lattice entry
- `templates/terminology-reconciliation.md` — blank reconciliation template
- `templates/cross-citation-matrix.md` — blank matrix
- `templates/coherence-check.md` — blank annual coherence sweep

---

## Integration Points

- `cognitive-awareness / Module 6` — cross-domain synthesis lives here
- `self-improvement / Module 5` — cross-skill integration mirrors cross-thesis integration
- `argument-architecture` — synthesis chapters use argument-architecture for structure
