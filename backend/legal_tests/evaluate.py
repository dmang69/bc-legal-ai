"""
Evaluate a LegalTest against matter EvidenceNodes.
Flags burden shift when E1+E2+E3 (or configured triggers) are satisfied.
"""

from __future__ import annotations

from typing import Optional

from architecture.evidence_node import EvidenceNode
from architecture.grounding import Citation
from architecture.legal_test import (
    ElementEvaluation,
    ElementEvidenceRole,
    ElementStatus,
    LegalTest,
    LegalTestEvaluation,
)
from backend.evidence.query import query_gaps
from backend.evidence.strength import apply_strength_to_node
from backend.grounding.citation_db import CitationDB
from backend.grounding.gate import flag_unverified_reference


def _node_matches_spec(
    node: EvidenceNode,
    tags: list[str],
    fact_keys: list[str],
    source_types: list[str],
) -> bool:
    tag_hit = bool(set(node.claim_tags) & set(tags)) if tags else False
    if tags and tag_hit:
        return True
    if fact_keys:
        node_keys = {kf.resolved_key() for kf in node.key_facts}
        for fk in fact_keys:
            norm = fk.replace("_", " ").lower()
            if norm in node_keys or fk.lower() in node_keys:
                return True
            # soft: keywords in extracted text
            blob = (node.extracted_text or "").lower()
            if any(part in blob for part in norm.split() if len(part) > 3):
                if tag_hit or not tags:
                    return True
    if source_types and node.source_type.value in source_types and tag_hit:
        return True
    # procedural heuristics
    blob = (
        (node.extracted_text or "")
        + " "
        + (node.source_file or "")
        + " "
        + " ".join(node.claim_tags)
    ).lower()
    return False


def _soft_match_element(node: EvidenceNode, element_id: str, description: str) -> bool:
    """Heuristic text match when structured specs are thin."""
    blob = (
        (node.extracted_text or "")
        + " "
        + (node.source_file or "")
        + " "
        + " ".join(node.claim_tags)
    ).lower()
    eid = element_id.lower()
    if "timely-dispute" in eid or "dispute" in description.lower():
        return any(
            w in blob
            for w in ("dispute", "rtb application", "filed", "application for dispute")
        )
    if "prior-complaint" in eid or "protected" in description.lower():
        return any(
            w in blob
            for w in (
                "repair",
                "complaint",
                "mold",
                "mould",
                "habitab",
                "request",
                "rtb",
            )
        ) or bool(
            set(node.claim_tags)
            & {"non_repair", "mold_hazard", "retaliatory_eviction", "city_enforcement"}
        )
    if "temporal-nexus" in eid or "timing" in description.lower():
        return "notice" in blob or "evict" in blob or "retaliatory_eviction" in node.claim_tags
    if "legitimate-cause" in eid or "pretextual" in description.lower():
        return "pretext" in blob or "false" in blob or "retaliatory_eviction" in node.claim_tags
    return False


def evaluate_legal_test(
    test: LegalTest,
    nodes: list[EvidenceNode],
    *,
    citation_db: Optional[CitationDB] = None,
) -> LegalTestEvaluation:
    for n in nodes:
        if n.strength_score is None:
            apply_strength_to_node(n)

    citation_ok = False
    citation_flag = None
    if citation_db is not None:
        probe = Citation(
            citation_id=test.citation_id,
            short_cite=test.citation,
        )
        resolved = citation_db.resolve(probe)
        if (
            resolved
            and resolved.status.value == "VERIFIED"
            and not resolved.superseded_by
        ):
            citation_ok = True
        else:
            flag = flag_unverified_reference(
                citation_db,
                resolved or probe,
                applies_to_hint=list(test.applies_to),
            )
            citation_flag = flag.to_dict()

    element_evals: list[ElementEvaluation] = []
    recommended: list[str] = []
    status_by_id: dict[str, ElementStatus] = {}

    for el in test.elements:
        matching: list[str] = []
        missing: list[str] = []

        specs = el.evidence or []
        required_specs = [
            e for e in specs if e.role == ElementEvidenceRole.REQUIRED
        ]
        adverse_specs = [e for e in specs if e.role == ElementEvidenceRole.ADVERSE]

        if specs:
            for spec in specs:
                if spec.role == ElementEvidenceRole.ADVERSE:
                    continue
                hits = [
                    n
                    for n in nodes
                    if (n.strength_score or 0) >= spec.min_strength
                    and (
                        _node_matches_spec(
                            n, spec.claim_tags, spec.fact_keys, spec.source_types
                        )
                        or _soft_match_element(n, el.element_id, el.description)
                    )
                ]
                for n in hits:
                    if n.node_id not in matching:
                        matching.append(n.node_id)
                if spec.role == ElementEvidenceRole.REQUIRED and not hits:
                    missing.append(
                        spec.description or f"Required evidence for {el.element_id}"
                    )
        else:
            # no specs — soft match only
            for n in nodes:
                if _soft_match_element(n, el.element_id, el.description):
                    matching.append(n.node_id)
            if el.required and not matching:
                missing.append(el.description)

        adverse_hits: list[str] = []
        for spec in adverse_specs:
            for n in nodes:
                if _node_matches_spec(
                    n, spec.claim_tags, spec.fact_keys, spec.source_types
                ):
                    adverse_hits.append(n.node_id)

        if el.required:
            if matching and not missing:
                status = ElementStatus.SATISFIED
                notes = ""
            elif matching and missing:
                status = ElementStatus.PARTIAL
                notes = "Some evidence present; required slots incomplete."
            elif matching:
                status = ElementStatus.SATISFIED
                notes = "Matched via structured or soft evidence rules."
            else:
                status = ElementStatus.NOT_SATISFIED
                notes = "No matching evidence for this element."
        else:
            # optional element
            if matching:
                status = ElementStatus.SATISFIED
                notes = f"Optional element supported (weight={el.weight})."
            else:
                status = ElementStatus.UNKNOWN
                notes = "Optional element — not established; does not block prima facie path."

        if adverse_hits:
            notes = (notes + " " if notes else "") + (
                f"Adverse evidence present: {', '.join(adverse_hits[:5])}."
            )
            if status == ElementStatus.SATISFIED and el.required:
                status = ElementStatus.PARTIAL

        if el.protected_activities and status != ElementStatus.SATISFIED:
            recommended.append(
                f"{el.element_id}: Upload proof of protected activity "
                f"({', '.join(el.protected_activities[:3])}…)."
            )
        for m in missing:
            recommended.append(f"{el.element_id}: {m}")

        status_by_id[el.element_id] = status
        element_evals.append(
            ElementEvaluation(
                element_id=el.element_id,
                status=status,
                required=el.required,
                evidence_type=el.evidence_type.value,
                weight=el.weight,
                matching_node_ids=matching,
                missing_evidence=missing,
                notes=notes,
            )
        )

    # Overall: all required elements SATISFIED → SATISFIED; any required missing → not
    required_statuses = [
        e.status for e in element_evals if e.required
    ]
    if required_statuses and all(s == ElementStatus.SATISFIED for s in required_statuses):
        overall = ElementStatus.SATISFIED
    elif any(
        s in (ElementStatus.SATISFIED, ElementStatus.PARTIAL) for s in required_statuses
    ):
        overall = ElementStatus.PARTIAL
    elif required_statuses:
        overall = ElementStatus.NOT_SATISFIED
    else:
        overall = ElementStatus.UNKNOWN

    # Burden shift
    burden_shift_triggered = False
    burden_shift_flag = None
    reasoning_flags: list[str] = []
    if test.burden_shift:
        triggers = test.burden_shift.triggers_when_elements
        if triggers and all(
            status_by_id.get(eid) == ElementStatus.SATISFIED for eid in triggers
        ):
            burden_shift_triggered = True
            burden_shift_flag = test.burden_shift.to_dict()
            reasoning_flags.append(test.burden_shift.reasoning_flag)
            reasoning_flags.append(
                "FLAG: Tenant appears to have made out E1+E2+E3 for burden-shift analysis. "
                "Landlord must be put to legitimate non-retaliatory cause. "
                "Confirm on current RTA s. 56 and case law before filing."
            )

    claim = test.applies_to[0] if test.applies_to else test.short_name
    gaps = [
        g.to_dict() for g in query_gaps(nodes, claim=claim, required_continuity=True)
    ]

    opposing = [
        f"{a.label} — {a.parenthetical} [{a.verification_status}]"
        for a in test.adverse_authority
    ]
    if burden_shift_triggered:
        opposing.append(
            "After burden shift: anticipate landlord evidence of independent legitimate cause "
            "(e.g. arrears, landlord use, demolition) — verify against notice type and record."
        )

    return LegalTestEvaluation(
        test_id=test.test_id,
        citation=test.citation,
        source=test.source,
        elements=element_evals,
        overall=overall,
        citation_gate_ok=citation_ok,
        citation_flag=citation_flag,
        gaps=gaps,
        recommended_uploads=list(dict.fromkeys(recommended)),
        burden_shift_triggered=burden_shift_triggered,
        burden_shift_flag=burden_shift_flag,
        reasoning_chain_flags=reasoning_flags,
        adverse_authority=[a.to_dict() for a in test.adverse_authority],
        opposing_anticipation=opposing,
    )
