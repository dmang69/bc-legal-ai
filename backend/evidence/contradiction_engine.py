"""
Pairwise key-fact contradiction engine for EvidenceNodes.

FOR each pair (A, B):
  IF shared fact_keys ≠ ∅ AND values conflict:
    CREATE CONTRADICTS edge
    FLAG contradiction_warning
    GENERATE ContradictionReport with resolution_strategy
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from architecture.evidence_node import (
    AuthenticityStatus,
    BestEvidenceRule,
    ContradictionReport,
    EvidenceNode,
    KeyFact,
    ResolutionStrategy,
)


# Polarity pairs that signal conflict when same fact_key carries opposite tokens
_NEGATION_PAIRS = (
    ("yes", "no"),
    ("true", "false"),
    ("fixed", "unfixed"),
    ("repaired", "unrepaired"),
    ("complied", "not complied"),
    ("paid", "unpaid"),
    ("served", "not served"),
    ("present", "absent"),
    ("mold", "no mold"),
    ("mould", "no mould"),
)


def _auth_rank(status: AuthenticityStatus) -> int:
    return {
        AuthenticityStatus.VERIFIED: 3,
        AuthenticityStatus.UNVERIFIED: 1,
        AuthenticityStatus.DISPUTED: 0,
    }[status]


def _evidence_rank(rule: BestEvidenceRule) -> int:
    return {
        BestEvidenceRule.ORIGINAL: 4,
        BestEvidenceRule.CERTIFIED_COPY: 3,
        BestEvidenceRule.DIGITAL: 2,
        BestEvidenceRule.PHOTOCOPY: 1,
    }[rule]


def _parse_date(iso: Optional[str]) -> Optional[datetime]:
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        try:
            return datetime.fromisoformat(iso[:10])
        except ValueError:
            return None


def facts_by_key(node: EvidenceNode) -> dict[str, KeyFact]:
    """Map fact_key → KeyFact (last write wins if duplicates)."""
    out: dict[str, KeyFact] = {}
    for kf in node.key_facts:
        out[kf.resolved_key()] = kf
    return out


def values_conflict(va: str, vb: str) -> bool:
    """True if two asserted values for the same key cannot both be true."""
    if not va or not vb:
        return False
    if va == vb:
        return False
    # Direct inequality of structured values
    # Soft: polarity / negation pairs
    for x, y in _NEGATION_PAIRS:
        if (x in va and y in vb) or (y in va and x in vb):
            return True
    # Numeric / date-like: different strings after norm already conflict
    # Require some substance difference (not mere rephrasing of same short token)
    if len(va) >= 2 and len(vb) >= 2:
        # If one is substring of other, treat as non-conflict (rephrase)
        if va in vb or vb in va:
            return False
        return True
    return va != vb


def choose_resolution(a: EvidenceNode, b: EvidenceNode, fa: KeyFact, fb: KeyFact) -> tuple[ResolutionStrategy, str]:
    """Pick resolution strategy from authentication strength and temporal context."""
    da = _parse_date(a.date_created or a.date_received)
    db = _parse_date(b.date_created or b.date_received)

    # Different times on same evolving fact → often both relevant
    if da and db and abs((da - db).days) >= 7:
        return (
            ResolutionStrategy.BOTH_RELEVANT,
            f"Dates differ by {abs((da - db).days)} days — condition may have changed",
        )

    ra, rb = _auth_rank(a.authenticity_status), _auth_rank(b.authenticity_status)
    if ra > rb + 0:
        if ra >= 3 and rb <= 1:
            return ResolutionStrategy.A_PRIORITY, "A has stronger authenticity status"
    if rb > ra:
        if rb >= 3 and ra <= 1:
            return ResolutionStrategy.B_PRIORITY, "B has stronger authenticity status"

    ea, eb = _evidence_rank(a.best_evidence_rule), _evidence_rank(b.best_evidence_rule)
    if ea >= eb + 2:
        return ResolutionStrategy.A_PRIORITY, "A closer to original under best-evidence ranking"
    if eb >= ea + 2:
        return ResolutionStrategy.B_PRIORITY, "B closer to original under best-evidence ranking"

    # Confidence gap alone is not enough to auto-resolve legal fact conflicts
    if abs(fa.confidence - fb.confidence) < 0.15:
        return ResolutionStrategy.NEEDS_HUMAN, "Comparable weight — human resolution required"

    return ResolutionStrategy.NEEDS_HUMAN, "Conflicting values with no clear authentication priority"


@dataclass
class ContradictionRunResult:
    reports: list[ContradictionReport] = field(default_factory=list)
    edges_created: int = 0
    nodes_flagged: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "reports": [r.to_dict() for r in self.reports],
            "edges_created": self.edges_created,
            "nodes_flagged": list(self.nodes_flagged),
        }


def detect_key_fact_contradictions(
    nodes: list[EvidenceNode],
    *,
    apply_edges: bool = True,
) -> ContradictionRunResult:
    """
    Pairwise scan of key_facts.

    Shared fact_key with conflicting values → CONTRADICTS + warning + report.
    """
    result = ContradictionRunResult()
    flagged: set[str] = set()

    for i, a in enumerate(nodes):
        fa_map = facts_by_key(a)
        if not fa_map:
            continue
        for b in nodes[i + 1 :]:
            fb_map = facts_by_key(b)
            shared = set(fa_map.keys()) & set(fb_map.keys())
            if not shared:
                continue
            for key in sorted(shared):
                fa, fb = fa_map[key], fb_map[key]
                va, vb = fa.resolved_value(), fb.resolved_value()
                if not values_conflict(va, vb):
                    continue

                strategy, note = choose_resolution(a, b, fa, fb)
                report = ContradictionReport(
                    fact=key,
                    node_a=a.node_id,
                    node_b=b.node_id,
                    node_a_claim=fa.value if fa.value is not None else fa.fact,
                    node_b_claim=fb.value if fb.value is not None else fb.fact,
                    resolution_strategy=strategy,
                    weight_difference=abs(fa.confidence - fb.confidence),
                    node_a_confidence=fa.confidence,
                    node_b_confidence=fb.confidence,
                    note=note,
                )
                result.reports.append(report)

                if apply_edges:
                    if b.node_id not in a.contradicts:
                        a.contradicts.append(b.node_id)
                        result.edges_created += 1
                    if a.node_id not in b.contradicts:
                        b.contradicts.append(a.node_id)
                        result.edges_created += 1
                    a.contradiction_warning = True
                    b.contradiction_warning = True
                    if key not in a.contradiction_fact_keys:
                        a.contradiction_fact_keys.append(key)
                    if key not in b.contradiction_fact_keys:
                        b.contradiction_fact_keys.append(key)
                    flagged.add(a.node_id)
                    flagged.add(b.node_id)

    result.nodes_flagged = sorted(flagged)
    return result
