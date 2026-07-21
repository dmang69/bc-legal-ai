# Cross-Domain Synthesis — Case Studies

**Module 6 in practice** (`cognitive-awareness`).

Validated links only. Bad synthesis is worse than none.

---

## Case 1 — Capability Tokens ↔ Legal Standing

| | |
|--|--|
| **Domain A** | OS security (IntentKernel / IKRL) |
| **Domain B** | Judicial review procedure |

**Shared structure:** Both answer: *who has authority to act on this object?*

| Domain A | Domain B |
|----------|----------|
| Capability token = cryptographic proof of authority to invoke an operation | Standing = legal proof of authority to bring a claim |

**Shared failure modes:**

| Failure | Capability world | Standing / procedure world |
|---------|------------------|----------------------------|
| Delegation without revocation | Capability leak | Running with expired standing / mootness / delay |
| Overbroad grant | Excessive permission | Overreach in pleading / improper parties |
| Missing verification | Forged token | Defective service / defective record |

**Non-obvious prediction:** Standing doctrine’s tests for real interest, sufficient connection, and prejudice suggest **concrete audit points** for capability grants (who holds interest, connection to resource, harm if grant abused).

**Practical use:** When designing OS capability models, import standing-style audit questions. When teaching standing, capability tokens are a clean analogy — **do not force** into court pleadings as if they were legal doctrine.

**Verified?** Y (structural; pedagogical / design use)

---

## Case 2 — Signal Signatures ↔ Evidence Bundles

| | |
|--|--|
| **Domain A** | Echo Calculus (five-component signature Σ) |
| **Domain B** | Trial / RTB evidence packaging |

**Shared structure:** Both compress complex phenomena into a fixed structure so downstream consumers can process them.

| Domain A (Σ quintuple) | Domain B (evidence bundle) |
|------------------------|----------------------------|
| source | author |
| medium | provenance |
| transform | alteration history |
| receiver | custodian |
| environment | context |

**Insight:** The bundle **is** a signature. Same properties matter — integrity, completeness, order-of-operations, reproducibility.

**Non-obvious prediction:** An exhibit that cannot survive the same integrity tests as a signature (broken chain, undated transform, unknown custodian) is **fragile evidence** — treat as discounted at RTB/court.

**Practical use:** Apply signature-integrity checks to evidence packaging (`bc-tenancy-procedure` Module 1): timestamps, provenance, no silent reconstruction.

**Verified?** Y (structural; maps to known evidence practice)

---

## Case 3 — Federated RL ↔ Distributed Litigation

| | |
|--|--|
| **Domain A** | AI-Native Internet thesis (federated reinforcement learning) |
| **Domain B** | Multi-party litigation coordination |

**Shared structure:** Independent agents make local decisions but must converge on shared strategy without full central control.

**Shared pathologies:**

| Pathology | Federated RL | Distributed litigation |
|-----------|--------------|------------------------|
| Dominant node | One client overweights global model | One co-party / counsel drives strategy |
| Drift | Local objectives diverge | Parties’ goals diverge mid-file |
| Silent defection | Client stops updating / poisons | Party goes silent / settles alone |

**Non-obvious prediction:** Gossip-style update cadence and “check for silent defection” protocols improve multi-party litigation coordination (scheduled status, shared issue list, explicit dissent logs).

**Practical use:** Design co-party check-ins like federated rounds — local work + shared consensus artifact. **Do not** claim RL math is admissible legal authority.

**Verified?** Y for structure/pathologies; N for mathematical identity (use as process metaphor only)

---

## When synthesis fails

Not every analogy is real.

```
□ Is the shared structure formal or superficial?
   Formal = same relations between elements
   Superficial = same words only
□ Does the mapping generate a NON-OBVIOUS prediction?
   If it only re-derives what you already know, it's decorative
□ Does the mapping survive a counterexample?
   Try to break it. If it breaks easily, don't use it
```

Only use synthesis that passes **all three**.

### Bad examples (do not use)

| Bad link | Why it fails |
|----------|--------------|
| “Court is just like a chat UI” | Superficial; stakes/rules not shared |
| “Always settle = always fold” | Ignores leverage; counterexamples abound |
| “Capability token = court order” | Formal mismatch (crypto grant ≠ judicial determination) |

---

## Related tenancy / counsel seams (short)

| Link | Type | Note |
|------|------|------|
| RTA substance ↔ RTB procedure | Hard handoff both ways | Evidence without sections incomplete |
| Retaliation (RTA) ↔ BCHRT discrimination | Dual-file | Complementary forums |
| JR standing ↔ IntentKernel capability | Pedagogical | Case 1 above |

---

## The Synthesis Library (running log)

Keep validated links. Format:

```
LINK
────
Domain A: [name]
Domain B: [name]
Shared structure: [what's actually the same]
Non-obvious prediction: [what the link generates]
Verified?: [Y/N]
Date: [YYYY-MM-DD]
Source: [user / design / practice]
```

Active log file: `synthesis-library.md`
