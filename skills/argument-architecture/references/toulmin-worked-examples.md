# Toulmin Model — Worked Examples

Toulmin structure applied to non-legal argumentation — thesis chapters,
technical proposals, research claims.

---

## Example 1 — Thesis Claim (Physics)

**CLAIM:** Thorium energy regimes require a distinct ontological framework
from uranium regimes.

**GROUNDS:**
- Thorium's fuel cycle produces materially different waste profiles
- The Th-232 → U-233 conversion pathway involves different neutron dynamics
- Regulatory categories built around uranium miscategorize thorium risks

**WARRANT:** Ontological categories track relevant causal structure. Where
causal structure differs materially, ontological categories must differ or
else miscategorization produces both scientific and regulatory error.

**BACKING:** The philosophy of science literature on natural kinds
(Boyd, Dupré) establishes that ontological categories are justified by
the causal-explanatory work they do, not by historical grouping.

**QUALIFIER:** This claim holds within regulatory ontology; whether it
extends to fundamental physical ontology is a separate question.

**REBUTTAL:** A critic could argue that both are fission fuels and the
distinction is one of degree, not kind. This fails because the pathway
differences are not merely quantitative — they produce categorically
different waste, categorically different proliferation risk profiles, and
categorically different reactor architectures.

---

## Example 2 — Technical Claim (OS Architecture)

**CLAIM:** Capability tokens are a superior authorization model to
access control lists for adversarial environments.

**GROUNDS:**
- ACLs require ambient authority (identity + lookup)
- Capabilities are unforgeable references
- Delegation in ACLs requires central trust; in capabilities it's local

**WARRANT:** Systems that minimize ambient authority minimize the
attack surface for confused deputy problems and privilege escalation.

**BACKING:** The object-capability security literature (Miller, Shapiro)
formally demonstrates the equivalence between ambient authority and the
confused deputy vulnerability.

**QUALIFIER:** This claim applies to systems where confused deputy
attacks are a realistic threat. In systems with a small, trusted user
base and no delegation, the practical difference is negligible.

**REBUTTAL:** ACLs are more familiar and integrate with existing
infrastructure. This is a legitimate practical concern but doesn't defeat
the security argument — it defeats the adoption argument. Where security
is the priority, capabilities win.

---

## Example 3 — Empirical Claim (AI-Native Internet)

**CLAIM:** Federated reinforcement learning outperforms centralized RL
for cognitive mesh routing in latency-constrained networks.

**GROUNDS:**
- Benchmark results (N=60) show federated RL achieving [X]% lower
  average latency than centralized baseline
- Federated approach avoids the round-trip to central coordinator
- Local models specialize to local traffic patterns

**WARRANT:** Where the environment is heterogeneous and latency is a
first-order concern, distributed decision-making outperforms centralized
decision-making because coordination overhead exceeds the marginal
benefit of global optimization.

**BACKING:** Amdahl's law and the CAP theorem both provide theoretical
grounding. Empirical work in distributed systems (Vogels on eventual
consistency) supports this in production.

**QUALIFIER:** This claim holds for networks with the traffic
characteristics in the benchmark. Networks with pathological patterns
(highly correlated global events) may still favor centralization.

**REBUTTAL:** A critic could argue federated approaches face convergence
issues and reproducibility problems. The benchmark controls for
convergence by measuring only after stable-state; reproducibility was
verified across five independent runs with matching results.

---

## The Warrant Is Where Arguments Live or Die

In each of these examples, the interesting move is the WARRANT — the
reasoning link between grounds and claim.

Weak arguments hide the warrant. Strong arguments state it.

When drafting, if you can't articulate the warrant, you haven't finished
the argument. You've finished the grounds. The claim is still floating.

### Warrant Types

| Type | Example |
|---|---|
| Causal | Where X causes Y, changes in X change Y |
| Analogical | Where case A is relevantly similar to case B, treatment of A extends to B |
| Definitional | Where X is a member of category C, properties of C attach to X |
| Statistical | Where the rate is P, expected outcomes match P |
| Authority | Where authority A speaks on matter M, and A is qualified for M, A's view is evidence |

Every warrant should be classifiable into one of these. If it can't be,
it's likely not a real warrant but a hidden assumption.
