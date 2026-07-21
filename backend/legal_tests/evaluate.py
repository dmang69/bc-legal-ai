"""
Evaluate a LegalTest against matter EvidenceNodes.
"""

from __future__ import annotations

from typing import Optional

from architecture.evidence_node import EvidenceNode
from architecture.legal_test import (
    ElementEvaluation,
    ElementEvidenceRole,
    ElementStatus,
    LegalTest,
    LegalTestEvaluation,
)
from architecture.grounding import Citation
from backend.evidence.query import query_gaps
from backend.evidence.strength import apply_strength_to_node
from backend.grounding.citation_db import CitationDB
from backend.grounding.gate import flag_unverified_reference


def _node_matches_spec(node: EvidenceNode, tags: list[str], fact_keys: list[str], source_types: list[str]) -> bool:
    if tags and not (set(node.claim_tags) & set(tags)):
        # also allow soft match on extracted text / activities later
        if not fact_keys and not source_types:
            return False
    if source_types and node.source_type.value not in source_types:
        if tags and (set(node.claim_tags) & set(tags)):
            pass  # tag match enough
        elif not tags:
            return False
    if fact_keys:
        node_keys = {kf.resolved_key() for kf in node.key_facts}
        if not (node_keys & {k.lower().replace("_", " ") for k in fact_keys}) and not (
            set(node.claim_tags) & set(tags)
        ):
            # allow tag overlap as proxy when key_facts not yet extracted
            if not (set(node.claim_tags) & set(tags)):
                return False
    if tags and (set(node.claim_tags) & set(tags)):
        return True
    if fact_keys:
        node_keys = {kf.resolved_key() for kf in node.key_facts}
        for fk in fact_keys:
            if fk.replace("_", " ") in node_keys or fk in node_keys:
                return True
    if source_types and node.source_type.value in source_types:
        return True
    return bool(tags and (set(node.claim_tags) & set(tags)))


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
        if resolved and resolved.status.value == "VERIFIED" and not resolved.superseded_by:
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

    for el in test.elements:
        matching: list[str] = []
        missing: list[str] = []
        required_specs = [e for e in el.evidence if e.role == ElementEvidenceRole.REQUIRED]
        supporting_specs = [e for e in el.evidence if e.role == ElementEvidenceRole.SUPPORTING]
        adverse_specs = [e for e in el.evidence if e.role == ElementEvidenceRole.ADVERSE]

        for spec in required_specs + supporting_specs:
            hits = [
                n
                for n in nodes
                if (n.strength_score or 0) >= spec.min_strength
                and _node_matches_spec(n, spec.claim_tags, spec.fact_keys, spec.source_types)
            ]
            for n in hits:
                if n.node_id not in matching:
                    matching.append(n.node_id)
            if spec.role == ElementEvidenceRole.REQUIRED and not hits:
                missing.append(spec.description or f"Required evidence for {el.element_id}")

        adverse_hits = []
        for spec in adverse_specs:
            for n in nodes:
                if _node_matches_spec(n, spec.claim_tags, spec.fact_keys, spec.source_types):
                    adverse_hits.append(n.node_id)

        if required_specs and not missing:
            status = ElementStatus.SATISFIED
            notes = ""
        elif matching and missing:
            status = ElementStatus.PARTIAL
            notes = "Some evidence present; required slots incomplete."
        elif matching and not required_specs:
            status = ElementStatus.PARTIAL
            notes = "Supporting evidence only; no REQUIRED specs defined."
        else:
            status = ElementStatus.NOT_SATISFIED
            notes = "No matching evidence for this element."

        if adverse_hits:
            notes = (notes + " " if notes else "") + (
                f"Adverse evidence present: {', '.join(adverse_hits[:5])}."
            )
            if status == ElementStatus.SATISFIED:
                status = ElementStatus.PARTIAL

        if el.protected_activities and status != ElementStatus.SATISFIED:
            recommended.append(
                f"{el.element_id}: Upload proof of protected activity "
                f"({', '.join(el.protected_activities[:3])}…)."
            )
        for m in missing:
            recommended.append(f"{el.element_id}: {m}")

        element_evals.append(
            ElementEvaluation(
                element_id=el.element_id,
                status=status,
                matching_node_ids=matching,
                missing_evidence=missing,
                notes=notes,
            )
        )

    statuses = [e.status for e in element_evals]
    if statuses and all(s == ElementStatus.SATISFIED for s in statuses):
        overall = ElementStatus.SATISFIED
    elif any(s in (ElementStatus.SATISFIED, ElementStatus.PARTIAL) for s in statuses):
        overall = ElementStatus.PARTIAL
    elif statuses:
        overall = ElementStatus.NOT_SATISFIED
    else:
        overall = ElementStatus.UNKNOWN

    # Continuity gaps for related claim tags
    claim = test.applies_to[0] if test.applies_to else test.short_name
    gaps = [g.to_dict() for g in query_gaps(nodes, claim=claim, required_continuity=True)]

    return LegalTestEvaluation(
        test_id=test.test_id,
        citation=test.citation,
        elements=element_evals,
        overall=overall,
        citation_gate_ok=citation_ok,
        citation_flag=citation_flag,
        gaps=gaps,
        recommended_uploads=list(dict.fromkeys(recommended)),
    )
