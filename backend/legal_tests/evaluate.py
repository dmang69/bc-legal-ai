"""
Evaluate a LegalTest against matter EvidenceNodes.

Produces narrative element blocks:
  ELEMENT E2-prior-complaint: SUPPORTED
    - Evidence nodes: ...
    - Summary: ...
"""

from __future__ import annotations

import re
from datetime import date
from typing import Optional

from architecture.evidence_node import EvidenceNode, SourceType
from architecture.grounding import Citation
from architecture.legal_test import (
    ElementEvaluation,
    ElementEvidenceRole,
    ElementEvidenceType,
    ElementStatus,
    InferenceStrength,
    LegalTest,
    LegalTestDisabledError,
    LegalTestEvaluation,
)
from backend.evidence.query import query_gaps
from backend.evidence.strength import apply_strength_to_node
from backend.grounding.citation_db import CitationDB
from backend.grounding.gate import flag_unverified_reference


def _parse_day(iso: Optional[str]) -> Optional[date]:
    if not iso:
        return None
    try:
        return date.fromisoformat(iso[:10])
    except ValueError:
        m = re.search(r"(20\d{2})-(\d{2})-(\d{2})", iso or "")
        if m:
            try:
                return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                return None
    return None


def _fmt_short(d: date) -> str:
    return d.strftime("%b %d").replace(" 0", " ")


def _display_id(node: EvidenceNode, index: int) -> str:
    """Prefer sequential node_id; also offer EM-### short label from matrix hash."""
    if node.node_id:
        return node.node_id
    return f"EM-{index:03d}"


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
            blob = (node.extracted_text or "").lower()
            if any(part in blob for part in norm.split() if len(part) > 3):
                if tag_hit or not tags:
                    return True
    if source_types and node.source_type.value in source_types and tag_hit:
        return True
    return False


def _soft_match_element(node: EvidenceNode, element_id: str, description: str) -> bool:
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
        return (
            "notice" in blob
            or "evict" in blob
            or "retaliatory_eviction" in node.claim_tags
        )
    if "legitimate-cause" in eid or "pretextual" in description.lower():
        return any(
            w in blob
            for w in (
                "pretext",
                "rcmp",
                "fine",
                "calls",
                "arrears",
                "legitimate",
                "police",
            )
        ) or "rent_issue" in node.claim_tags
    return False


def _is_counter_to_adverse(node: EvidenceNode) -> bool:
    blob = ((node.extracted_text or "") + " " + (node.source_file or "")).lower()
    return any(
        w in blob
        for w in (
            "no conviction",
            "no convictions",
            "not convicted",
            "roommate's guest",
            "roommates guest",
            "acquitted",
            "charges dropped",
            "not charged",
        )
    )


def _is_adverse_noise_crime(node: EvidenceNode) -> bool:
    """Landlord-cause style adverse record (RCMP/fines) — not tenant exculpatory notes."""
    if _is_counter_to_adverse(node):
        return False
    blob = ((node.extracted_text or "") + " " + (node.source_file or "")).lower()
    return any(
        w in blob
        for w in (
            "rcmp",
            "police",
            "fine",
            "fines",
            "bylaw",
            "400+",
            "400 +",
            "calls to the property",
        )
    ) or (
        "city_enforcement" in node.claim_tags
        and not _is_counter_to_adverse(node)
    )


def _summarize_nodes(nodes: list[EvidenceNode], element_id: str) -> str:
    if not nodes:
        return ""
    eid = element_id.lower()
    if "prior-complaint" in eid:
        n_email = sum(
            1
            for n in nodes
            if n.source_type in (SourceType.EMAIL, SourceType.TEXT_MESSAGE)
            or "email" in (n.source_file or "").lower()
        )
        if n_email:
            return (
                f"{n_email} email(s)/message(s) complaining about mold/habitability "
                f"or repairs (plus related record items as tagged)."
            )
        return f"{len(nodes)} evidence item(s) showing protected activity / complaint."
    if "timely-dispute" in eid:
        return f"{len(nodes)} procedural record(s) of dispute filing / RTB process."
    if "temporal-nexus" in eid:
        return (
            f"{len(nodes)} item(s) establishing sequence of complaint(s) and eviction notice."
        )
    if "legitimate-cause" in eid:
        return f"{len(nodes)} item(s) touching landlord cause / pretext analysis."
    # generic
    kinds: dict[str, int] = {}
    for n in nodes:
        kinds[n.source_type.value] = kinds.get(n.source_type.value, 0) + 1
    parts = [f"{v} {k.lower().replace('_', ' ')}" for k, v in kinds.items()]
    return f"{len(nodes)} supporting item(s): " + ", ".join(parts)


def _has_word(blob: str, word: str) -> bool:
    """Whole-word match — avoid 'evict' matching inside 'retaliatory_eviction'."""
    return re.search(rf"\b{re.escape(word)}\b", blob) is not None


def _temporal_nexus_enrichment(
    matching: list[EvidenceNode],
    all_nodes: list[EvidenceNode],
) -> tuple[Optional[int], str, InferenceStrength]:
    """Gap between last complaint-like event and notice."""
    complaints: list[tuple[date, EvidenceNode]] = []
    notices: list[tuple[date, EvidenceNode]] = []
    for n in all_nodes:
        d = _parse_day(n.date_created or n.date_received)
        if not d:
            continue
        text = (n.extracted_text or "").lower()
        tags = set(n.claim_tags)
        is_complaint = any(
            w in text
            for w in ("repair", "complaint", "complain", "mold", "mould", "habitab", "request")
        ) or bool(tags & {"non_repair", "mold_hazard"})
        # Notice to end / eviction step — require notice language in text or notice form type
        is_notice = (
            _has_word(text, "notice")
            or "notice to end" in text
            or _has_word(text, "eviction")
            or (
                n.source_type == SourceType.GOVERNMENT_CORRESPONDENCE
                and (
                    _has_word(text, "notice")
                    or "tenancy" in text
                    or "retaliatory_eviction" in tags
                )
            )
        )
        # Pure complaint emails should not be treated as notices
        if is_complaint and not is_notice:
            complaints.append((d, n))
        if is_notice and not (
            is_complaint and n.source_type in (SourceType.EMAIL, SourceType.TEXT_MESSAGE)
        ):
            notices.append((d, n))
        elif is_notice:
            notices.append((d, n))

    if not complaints or not notices:
        # fall back to matching set span
        dated = []
        for n in matching:
            d = _parse_day(n.date_created or n.date_received)
            if d:
                dated.append(d)
        if len(dated) >= 2:
            dated.sort()
            gap = (dated[-1] - dated[0]).days
            label = (
                f"Gap across supporting evidence dates: {gap} days "
                f"({_fmt_short(dated[0])} → {_fmt_short(dated[-1])})"
            )
            strength = (
                InferenceStrength.HIGH
                if gap <= 30
                else InferenceStrength.MEDIUM
                if gap <= 90
                else InferenceStrength.LOW
            )
            return gap, label, strength
        return None, "", InferenceStrength.UNKNOWN

    complaints.sort(key=lambda x: x[0])
    notices.sort(key=lambda x: x[0])
    last_c, _ = complaints[-1]
    # first notice after last complaint, else last notice
    after = [n for n in notices if n[0] >= last_c]
    notice_d = after[0][0] if after else notices[-1][0]
    gap = (notice_d - last_c).days
    if gap < 0:
        gap = abs(gap)
    label = (
        f"Gap between last complaint ({_fmt_short(last_c)}) and notice "
        f"({_fmt_short(notice_d)}): {gap} days"
    )
    # Heuristic ranges for "HIGH" nexus (not case law holdings)
    if gap <= 21:
        strength = InferenceStrength.HIGH
    elif gap <= 60:
        strength = InferenceStrength.MEDIUM
    else:
        strength = InferenceStrength.LOW
    return gap, label, strength


def _report_label(
    status: ElementStatus,
    *,
    weighted: bool,
    conflicted: bool,
    human: bool,
) -> tuple[str, ElementStatus]:
    if human or conflicted:
        return "CONFLICTED", ElementStatus.CONFLICTED
    if status in (ElementStatus.SATISFIED, ElementStatus.SUPPORTED):
        if weighted:
            return "SUPPORTED (WEIGHTED)", ElementStatus.SUPPORTED_WEIGHTED
        return "SUPPORTED", ElementStatus.SUPPORTED
    if status == ElementStatus.PARTIAL:
        return "PARTIAL", ElementStatus.PARTIAL
    if status == ElementStatus.NOT_SATISFIED:
        return "NOT SUPPORTED", ElementStatus.NOT_SATISFIED
    return "UNKNOWN", ElementStatus.UNKNOWN


def evaluate_legal_test(
    test: LegalTest,
    nodes: list[EvidenceNode],
    *,
    citation_db: Optional[CitationDB] = None,
    allow_disabled: bool = False,
) -> LegalTestEvaluation:
    if test.disabled and not allow_disabled:
        raise LegalTestDisabledError(
            test.disabled_reason
            or f"Legal test {test.test_id} is DISABLED and cannot be evaluated."
        )
    for n in nodes:
        if n.strength_score is None:
            apply_strength_to_node(n)

    nodes_by_id = {n.node_id: n for n in nodes}

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
        matching_nodes: list[EvidenceNode] = []
        missing: list[str] = []
        specs = el.evidence or []
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
                    if n not in matching_nodes:
                        matching_nodes.append(n)
                if spec.role == ElementEvidenceRole.REQUIRED and not hits:
                    missing.append(
                        spec.description or f"Required evidence for {el.element_id}"
                    )
        else:
            for n in nodes:
                if _soft_match_element(n, el.element_id, el.description):
                    matching_nodes.append(n)
            if el.required and not matching_nodes:
                missing.append(el.description)

        matching = [n.node_id for n in matching_nodes]
        display_ids = [
            _display_id(n, i + 1) for i, n in enumerate(matching_nodes)
        ]

        adverse_nodes: list[EvidenceNode] = []
        for spec in adverse_specs:
            for n in nodes:
                if _node_matches_spec(
                    n, spec.claim_tags, spec.fact_keys, spec.source_types
                ):
                    adverse_nodes.append(n)
        # E4: also detect RCMP/fines style adverse + counter
        adverse_labels: list[str] = []
        counter_labels: list[str] = []
        if "legitimate-cause" in el.element_id.lower():
            for n in nodes:
                if _is_adverse_noise_crime(n):
                    adverse_nodes.append(n)
                    label = n.source_file or n.node_id
                    blob = (n.extracted_text or label).strip()
                    if len(blob) > 60:
                        blob = blob[:57] + "…"
                    adverse_labels.append(blob or label)
                if _is_counter_to_adverse(n):
                    blob = (n.extracted_text or n.source_file or n.node_id).strip()
                    if len(blob) > 60:
                        blob = blob[:57] + "…"
                    counter_labels.append(blob)

        for n in adverse_nodes:
            if n.node_id not in matching and "legitimate-cause" not in el.element_id.lower():
                pass  # adverse for required elements handled below

        # Base status
        if el.required:
            if matching_nodes and not missing:
                status = ElementStatus.SATISFIED
                notes = ""
            elif matching_nodes and missing:
                status = ElementStatus.PARTIAL
                notes = "Some evidence present; required slots incomplete."
            elif matching_nodes:
                status = ElementStatus.SATISFIED
                notes = "Matched via structured or soft evidence rules."
            else:
                status = ElementStatus.NOT_SATISFIED
                notes = "No matching evidence for this element."
        else:
            if matching_nodes or adverse_labels or counter_labels:
                status = ElementStatus.SATISFIED
                notes = f"Optional element engaged (weight={el.weight})."
            else:
                status = ElementStatus.UNKNOWN
                notes = "Optional element — not established."

        conflicted = False
        human = False
        # Conflict when adverse + counter both present on E4-style elements
        if adverse_labels and counter_labels:
            conflicted = True
            human = True
            status = ElementStatus.CONFLICTED
            notes = (
                "Adverse and counter-evidence both present. "
                "Engine cannot resolve — requires lawyer review."
            )
        elif adverse_labels and "legitimate-cause" in el.element_id.lower():
            conflicted = True
            human = True
            status = ElementStatus.CONFLICTED
            if not counter_labels:
                notes = (
                    "Adverse evidence of legitimate cause appears on the record. "
                    "Requires lawyer judgment whether pretextual."
                )

        if el.protected_activities and status not in (
            ElementStatus.SATISFIED,
            ElementStatus.SUPPORTED,
            ElementStatus.SUPPORTED_WEIGHTED,
        ):
            recommended.append(
                f"{el.element_id}: Upload proof of protected activity "
                f"({', '.join(el.protected_activities[:3])}…)."
            )
        for m in missing:
            recommended.append(f"{el.element_id}: {m}")

        # Temporal nexus enrichment
        gap_days = None
        gap_label = ""
        inf_strength = None
        if el.evidence_type == ElementEvidenceType.INFERENTIAL and matching_nodes:
            if "temporal" in el.element_id.lower() or "nexus" in el.element_id.lower():
                gap_days, gap_label, inf_s = _temporal_nexus_enrichment(
                    matching_nodes, nodes
                )
                inf_strength = inf_s.value if inf_s != InferenceStrength.UNKNOWN else None

        weighted = (
            el.evidence_type == ElementEvidenceType.INFERENTIAL
            and el.weight is not None
            and status
            in (
                ElementStatus.SATISFIED,
                ElementStatus.SUPPORTED,
                ElementStatus.SUPPORTED_WEIGHTED,
            )
            and not conflicted
        )

        report_label, report_status = _report_label(
            status, weighted=weighted, conflicted=conflicted, human=human
        )
        # Keep SATISFIED in status_by_id for burden shift when supported
        gate_status = (
            ElementStatus.SATISFIED
            if report_status
            in (
                ElementStatus.SUPPORTED,
                ElementStatus.SUPPORTED_WEIGHTED,
                ElementStatus.SATISFIED,
            )
            else report_status
            if report_status
            not in (ElementStatus.CONFLICTED, ElementStatus.REQUIRES_HUMAN_JUDGMENT)
            else ElementStatus.PARTIAL
        )
        if conflicted:
            gate_status = ElementStatus.PARTIAL  # does not block burden on E1-E3
            if el.required:
                gate_status = ElementStatus.PARTIAL

        status_by_id[el.element_id] = (
            ElementStatus.SATISFIED
            if report_status
            in (ElementStatus.SUPPORTED, ElementStatus.SUPPORTED_WEIGHTED)
            else gate_status
        )

        summary = _summarize_nodes(matching_nodes, el.element_id)
        if conflicted and not summary:
            summary = "Record contains competing narratives on landlord cause."

        element_evals.append(
            ElementEvaluation(
                element_id=el.element_id,
                status=report_status
                if report_status
                not in (ElementStatus.SUPPORTED, ElementStatus.SUPPORTED_WEIGHTED)
                else (
                    ElementStatus.SUPPORTED_WEIGHTED
                    if weighted
                    else ElementStatus.SUPPORTED
                ),
                required=el.required,
                evidence_type=el.evidence_type.value,
                weight=el.weight,
                matching_node_ids=matching,
                display_node_ids=display_ids,
                missing_evidence=missing,
                notes=notes,
                report_label=report_label,
                summary=summary,
                adverse_evidence=adverse_labels,
                counter_evidence=counter_labels,
                temporal_gap_days=gap_days,
                temporal_gap_label=gap_label,
                inference_strength=inf_strength,
                human_judgment_required=human,
            )
        )

    required_statuses = [e.status for e in element_evals if e.required]
    # treat SUPPORTED* as satisfied for overall
    def _ok(s: ElementStatus) -> bool:
        return s in (
            ElementStatus.SATISFIED,
            ElementStatus.SUPPORTED,
            ElementStatus.SUPPORTED_WEIGHTED,
        )

    if required_statuses and all(_ok(s) for s in required_statuses):
        overall = ElementStatus.SATISFIED
    elif any(
        _ok(s) or s == ElementStatus.PARTIAL for s in required_statuses
    ):
        overall = ElementStatus.PARTIAL
    elif required_statuses:
        overall = ElementStatus.NOT_SATISFIED
    else:
        overall = ElementStatus.UNKNOWN

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
    for e in element_evals:
        if e.human_judgment_required:
            opposing.append(
                f"{e.element_id}: CONFLICTED — requires human judgment before reliance."
            )

    result = LegalTestEvaluation(
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
    result.element_report = result.format_element_report()
    return result
