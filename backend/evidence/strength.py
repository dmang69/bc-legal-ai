"""
Compute and assign strength scores / tiers for EvidenceNodes and matrix rows.
"""

from __future__ import annotations

from architecture.evidence_node import (
    AuthenticityStatus,
    BestEvidenceRule,
    EvidenceNode,
    PrivilegeClass,
)
from architecture.schemas import EvidenceItem
from architecture.strength import (
    StrengthAssessment,
    StrengthTier,
    assess_score,
    score_to_tier,
)


def compute_node_strength(node: EvidenceNode) -> StrengthAssessment:
    """
    Heuristic composite score from authenticity, best-evidence form,
    key-fact confidence, corroboration, and risk flags.
    """
    score = 0.35  # baseline UNVERIFIED digital
    factors: list[str] = ["baseline"]
    risks: list[str] = []

    # Authenticity
    if node.authenticity_status == AuthenticityStatus.VERIFIED:
        score += 0.28
        factors.append("authenticity_verified")
    elif node.authenticity_status == AuthenticityStatus.DISPUTED:
        score -= 0.20
        factors.append("authenticity_disputed")
        risks.append("authenticity_disputed")
    else:
        factors.append("authenticity_unverified")
        risks.append("authenticity_unverified")

    # Best evidence form
    be = {
        BestEvidenceRule.ORIGINAL: 0.18,
        BestEvidenceRule.CERTIFIED_COPY: 0.14,
        BestEvidenceRule.DIGITAL: 0.08,
        BestEvidenceRule.PHOTOCOPY: 0.04,
    }[node.best_evidence_rule]
    score += be
    factors.append(f"best_evidence_{node.best_evidence_rule.value.lower()}")

    # Key fact confidence (average if present)
    if node.key_facts:
        avg_c = sum(k.confidence for k in node.key_facts) / len(node.key_facts)
        score += 0.15 * avg_c
        factors.append(f"key_facts_avg_confidence={avg_c:.2f}")
    else:
        risks.append("no_key_facts_extracted")

    # Corroboration boost (cap)
    n_corr = len(node.corroborates)
    if n_corr:
        boost = min(0.12, 0.04 * n_corr)
        score += boost
        factors.append(f"corroboration_links={n_corr}")

    # Contradiction penalty
    if node.contradiction_warning or node.contradicts:
        score -= 0.15
        factors.append("contradiction_flag")
        risks.append("contradiction_with_other_nodes")

    # Hearsay
    if node.hearsay_flag and not node.hearsay_exception:
        score -= 0.12
        factors.append("hearsay_unexcepted")
        risks.append("hearsay_objection_risk")
    elif node.hearsay_flag and node.hearsay_exception:
        score -= 0.04
        factors.append(f"hearsay_exception_claimed={node.hearsay_exception}")
        risks.append("hearsay_exception_must_be_verified")

    # Admissibility assessment
    if node.admissibility_assessment.likely_admissible:
        score += 0.08
        factors.append("admissibility_likely")
    if node.admissibility_assessment.risks:
        score -= min(0.10, 0.03 * len(node.admissibility_assessment.risks))
        risks.extend(node.admissibility_assessment.risks[:3])

    # Privilege protected is not weaker legally, but may be export-blocked
    if node.privilege_class == PrivilegeClass.PROTECTED:
        factors.append("privilege_protected")
        risks.append("production_gate_required")

    score = max(0.0, min(1.0, score))
    return assess_score(score, factors=factors, risks=risks)


def apply_strength_to_node(node: EvidenceNode) -> StrengthAssessment:
    """Write strength_score / strength_tier onto node; return assessment."""
    assessment = compute_node_strength(node)
    node.strength_score = assessment.score
    node.strength_tier = assessment.tier.value
    return assessment


def apply_strength_to_item(item: EvidenceItem, assessment: StrengthAssessment) -> None:
    """Mirror score onto matrix hearing_relevance for binder sorting."""
    item.hearing_relevance = assessment.score


def tier_buckets(nodes: list[EvidenceNode]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {"A": [], "B": [], "C": [], "D": []}
    for n in nodes:
        score = getattr(n, "strength_score", None)
        if score is None:
            assessment = apply_strength_to_node(n)
            tier = assessment.tier.value
        else:
            tier = score_to_tier(float(score)).value
        buckets.setdefault(tier, []).append(n.node_id)
    return buckets


def format_strength_report(nodes: list[EvidenceNode]) -> str:
    lines = [
        "EVIDENCE STRENGTH TIERS:",
        "",
        "0.80–1.00 → TIER A (Primary evidence — build case around these)",
        "0.60–0.79 → TIER B (Supporting evidence — reinforces Tier A)",
        "0.40–0.59 → TIER C (Corroborating — adds texture but not load-bearing)",
        "0.00–0.39 → TIER D (Weak — use only if no alternative, flag risks)",
        "",
    ]
    by_tier: dict[str, list[EvidenceNode]] = {"A": [], "B": [], "C": [], "D": []}
    for n in nodes:
        if getattr(n, "strength_score", None) is None:
            apply_strength_to_node(n)
        tier = n.strength_tier or score_to_tier(n.strength_score or 0).value
        by_tier.setdefault(tier, []).append(n)

    for tier in ("A", "B", "C", "D"):
        group = sorted(by_tier.get(tier, []), key=lambda x: -(x.strength_score or 0))
        lines.append(f"### TIER {tier} ({StrengthTier(tier).range_label})")
        if not group:
            lines.append("- (none)")
        for n in group:
            score = n.strength_score if n.strength_score is not None else 0.0
            name = n.source_file or n.node_id
            lines.append(f"- {n.node_id} · {score:.2f} · {name}")
            if tier == "D":
                lines.append("  ⚠ Weak — flag risks if used")
        lines.append("")
    lines.append(
        "> Scores are workbench heuristics for case construction priority. "
        "Not determinations of admissibility or weight by a tribunal."
    )
    return "\n".join(lines)
