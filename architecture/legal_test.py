"""
LegalTest — structured multi-element legal tests for argument assembly.

Elements require evidence mapping; statutory pins must resolve in CitationDB.
Not legal advice. Element lists and adverse-authority notes are workbench
scaffolds — re-verify every pin and case on BC Laws / CanLII before filing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ElementEvidenceRole(str, Enum):
    REQUIRED = "REQUIRED"
    SUPPORTING = "SUPPORTING"
    ADVERSE = "ADVERSE"


class ElementEvidenceType(str, Enum):
    """How the element is typically proven."""

    PROCEDURAL = "procedural"
    SUBSTANTIVE = "substantive"
    INFERENTIAL = "inferential"


class ElementStatus(str, Enum):
    """Internal + report-facing statuses."""

    SATISFIED = "SATISFIED"  # maps to SUPPORTED
    PARTIAL = "PARTIAL"
    NOT_SATISFIED = "NOT_SATISFIED"
    UNKNOWN = "UNKNOWN"
    # Report labels (also valid status values)
    SUPPORTED = "SUPPORTED"
    SUPPORTED_WEIGHTED = "SUPPORTED_WEIGHTED"
    CONFLICTED = "CONFLICTED"
    REQUIRES_HUMAN_JUDGMENT = "REQUIRES_HUMAN_JUDGMENT"


class InferenceStrength(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


@dataclass
class ElementEvidenceSpec:
    """Optional structured matchers for auto-evaluation against EvidenceNodes."""

    role: ElementEvidenceRole = ElementEvidenceRole.REQUIRED
    claim_tags: list[str] = field(default_factory=list)
    fact_keys: list[str] = field(default_factory=list)
    source_types: list[str] = field(default_factory=list)
    min_strength: float = 0.4
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role.value,
            "claim_tags": list(self.claim_tags),
            "fact_keys": list(self.fact_keys),
            "source_types": list(self.source_types),
            "min_strength": self.min_strength,
            "description": self.description,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ElementEvidenceSpec":
        role = data.get("role", ElementEvidenceRole.REQUIRED.value)
        return ElementEvidenceSpec(
            role=ElementEvidenceRole(role)
            if not isinstance(role, ElementEvidenceRole)
            else role,
            claim_tags=list(data.get("claim_tags") or []),
            fact_keys=list(data.get("fact_keys") or []),
            source_types=list(data.get("source_types") or []),
            min_strength=float(data.get("min_strength") or 0.4),
            description=str(data.get("description") or ""),
        )


@dataclass
class LegalTestElement:
    element_id: str  # e.g. E1-timely-dispute
    description: str
    evidence_type: ElementEvidenceType = ElementEvidenceType.SUBSTANTIVE
    required: bool = True
    weight: Optional[float] = None  # contribution when inferential / optional
    protected_activities: list[str] = field(default_factory=list)
    evidence: list[ElementEvidenceSpec] = field(default_factory=list)
    notes: str = ""

    # aliases
    @property
    def id(self) -> str:
        return self.element_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.element_id,
            "element_id": self.element_id,
            "description": self.description,
            "evidence_type": self.evidence_type.value,
            "required": self.required,
            "weight": self.weight,
            "protected_activities": list(self.protected_activities),
            "evidence": [e.to_dict() for e in self.evidence],
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "LegalTestElement":
        eid = str(data.get("id") or data.get("element_id") or "")
        et = data.get("evidence_type", ElementEvidenceType.SUBSTANTIVE.value)
        return LegalTestElement(
            element_id=eid,
            description=str(data.get("description") or ""),
            evidence_type=(
                ElementEvidenceType(et)
                if not isinstance(et, ElementEvidenceType)
                else et
            ),
            required=bool(data.get("required", True)),
            weight=data.get("weight"),
            protected_activities=list(data.get("protected_activities") or []),
            evidence=[
                ElementEvidenceSpec.from_dict(x) for x in (data.get("evidence") or [])
            ],
            notes=str(data.get("notes") or ""),
        )


@dataclass
class AdverseAuthorityNote:
    """
    Illustrative counter-authority label for Devil's Advocate.

    NOT a verified Citation — must be checked on CanLII and may trigger
    UNVERIFIED CITATION FLAG if used in grounded output.
    """

    label: str
    parenthetical: str = ""
    verification_status: str = "UNVERIFIED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "parenthetical": self.parenthetical,
            "verification_status": self.verification_status,
        }

    @staticmethod
    def from_dict(data: dict[str, Any] | str) -> "AdverseAuthorityNote":
        if isinstance(data, str):
            # "Case v Name — holding summary"
            if "—" in data:
                lab, par = data.split("—", 1)
                return AdverseAuthorityNote(
                    label=lab.strip(), parenthetical=par.strip()
                )
            if " - " in data:
                lab, par = data.split(" - ", 1)
                return AdverseAuthorityNote(
                    label=lab.strip(), parenthetical=par.strip()
                )
            return AdverseAuthorityNote(label=data.strip())
        return AdverseAuthorityNote(
            label=str(data.get("label") or ""),
            parenthetical=str(data.get("parenthetical") or ""),
            verification_status=str(data.get("verification_status") or "UNVERIFIED"),
        )


@dataclass
class BurdenShiftRule:
    """When tenant makes out a prima facie case, burden may shift."""

    triggers_when_elements: list[str]  # element ids that must be SATISFIED
    shifts_to: str  # e.g. "landlord"
    description: str
    reasoning_flag: str = "BURDEN_SHIFT"

    def to_dict(self) -> dict[str, Any]:
        return {
            "triggers_when_elements": list(self.triggers_when_elements),
            "shifts_to": self.shifts_to,
            "description": self.description,
            "reasoning_flag": self.reasoning_flag,
        }


@dataclass
class LegalTest:
    test_id: str
    citation: str
    elements: list[LegalTestElement] = field(default_factory=list)
    jurisdiction: str = "BC"
    source: str = ""  # full official cite line
    short_name: str = ""
    applies_to: list[str] = field(default_factory=list)
    citation_id: Optional[str] = None
    burden: str = "balance of probabilities"
    adverse_authority: list[AdverseAuthorityNote] = field(default_factory=list)
    burden_shift: Optional[BurdenShiftRule] = None
    notes: str = ""
    verification_note: str = (
        "Legal test scaffold for workbench analysis. Verify every statutory pin "
        "and case on BC Laws / CanLII before filing. Not legal advice."
    )

    # aliases
    @property
    def id(self) -> str:
        return self.test_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.test_id,
            "test_id": self.test_id,
            "jurisdiction": self.jurisdiction,
            "source": self.source,
            "citation": self.citation,
            "citation_id": self.citation_id,
            "short_name": self.short_name or self.test_id,
            "applies_to": list(self.applies_to),
            "burden": self.burden,
            "elements": [e.to_dict() for e in self.elements],
            "adverse_authority": [a.to_dict() for a in self.adverse_authority],
            "burden_shift": self.burden_shift.to_dict() if self.burden_shift else None,
            "notes": self.notes,
            "verification_note": self.verification_note,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "LegalTest":
        tid = str(data.get("id") or data.get("test_id") or "")
        bs = data.get("burden_shift")
        burden_shift = None
        if isinstance(bs, dict):
            burden_shift = BurdenShiftRule(
                triggers_when_elements=list(bs.get("triggers_when_elements") or []),
                shifts_to=str(bs.get("shifts_to") or "landlord"),
                description=str(bs.get("description") or ""),
                reasoning_flag=str(bs.get("reasoning_flag") or "BURDEN_SHIFT"),
            )
        adv = data.get("adverse_authority") or []
        return LegalTest(
            test_id=tid,
            citation=str(data.get("citation") or ""),
            elements=[
                LegalTestElement.from_dict(x) for x in (data.get("elements") or [])
            ],
            jurisdiction=str(data.get("jurisdiction") or "BC"),
            source=str(data.get("source") or ""),
            short_name=str(data.get("short_name") or ""),
            applies_to=list(data.get("applies_to") or []),
            citation_id=data.get("citation_id"),
            burden=str(data.get("burden") or "balance of probabilities"),
            adverse_authority=[AdverseAuthorityNote.from_dict(a) for a in adv],
            burden_shift=burden_shift,
            notes=str(data.get("notes") or ""),
            verification_note=str(
                data.get("verification_note")
                or LegalTest(test_id="", citation="").verification_note
            ),
        )


@dataclass
class ElementEvaluation:
    """
    Per-element evaluation with narrative report fields.

    Example:
      ELEMENT E2-prior-complaint: SUPPORTED
        - Evidence nodes: EM-041, EM-044, EM-047
        - Summary: Three emails to landlord complaining about mold/habitability
    """

    element_id: str
    status: ElementStatus
    required: bool = True
    evidence_type: str = ""
    weight: Optional[float] = None
    matching_node_ids: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    notes: str = ""
    # Report enrichment
    report_label: str = ""  # SUPPORTED | SUPPORTED (WEIGHTED) | CONFLICTED | ...
    summary: str = ""
    adverse_evidence: list[str] = field(default_factory=list)
    counter_evidence: list[str] = field(default_factory=list)
    temporal_gap_days: Optional[int] = None
    temporal_gap_label: str = ""  # e.g. "Gap between last complaint (Oct 28) and notice (Nov 12): 15 days"
    inference_strength: Optional[str] = None  # HIGH | MEDIUM | LOW
    human_judgment_required: bool = False
    display_node_ids: list[str] = field(default_factory=list)  # EM-041 style or node_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "element_id": self.element_id,
            "status": self.status.value,
            "report_label": self.report_label or self.status.value,
            "required": self.required,
            "evidence_type": self.evidence_type,
            "weight": self.weight,
            "matching_node_ids": list(self.matching_node_ids),
            "display_node_ids": list(self.display_node_ids or self.matching_node_ids),
            "missing_evidence": list(self.missing_evidence),
            "notes": self.notes,
            "summary": self.summary,
            "adverse_evidence": list(self.adverse_evidence),
            "counter_evidence": list(self.counter_evidence),
            "temporal_gap_days": self.temporal_gap_days,
            "temporal_gap_label": self.temporal_gap_label,
            "inference_strength": self.inference_strength,
            "human_judgment_required": self.human_judgment_required,
        }

    def format_block(self) -> str:
        label = self.report_label or self.status.value
        lines = [f"ELEMENT {self.element_id}: {label}"]
        nodes = self.display_node_ids or self.matching_node_ids
        if nodes:
            lines.append(f"  - Evidence nodes: {', '.join(nodes)}")
        if self.summary:
            lines.append(f"  - Summary: {self.summary}")
        if self.temporal_gap_label:
            lines.append(f"  - {self.temporal_gap_label}")
        if self.inference_strength:
            lines.append(
                f"  - Inference strength: {self.inference_strength}"
                + (
                    " (within range of cases where courts found nexus)"
                    if self.inference_strength == "HIGH"
                    and "temporal" in self.element_id
                    else ""
                )
            )
        if self.adverse_evidence:
            lines.append(
                f"  - Adverse evidence: {'; '.join(self.adverse_evidence)}"
            )
        if self.counter_evidence:
            lines.append(
                f"  - Counter-evidence: {'; '.join(self.counter_evidence)}"
            )
        if self.human_judgment_required or self.status in (
            ElementStatus.CONFLICTED,
            ElementStatus.REQUIRES_HUMAN_JUDGMENT,
        ):
            lines.append("  - Engine cannot resolve — flags for lawyer review")
            lines.append("  - STATUS: REQUIRES HUMAN JUDGMENT")
        if self.missing_evidence and not nodes:
            for m in self.missing_evidence[:3]:
                lines.append(f"  - Missing: {m}")
        return "\n".join(lines)


@dataclass
class LegalTestEvaluation:
    test_id: str
    citation: str
    source: str = ""
    elements: list[ElementEvaluation] = field(default_factory=list)
    overall: ElementStatus = ElementStatus.UNKNOWN
    citation_gate_ok: bool = False
    citation_flag: Optional[dict[str, Any]] = None
    gaps: list[dict[str, Any]] = field(default_factory=list)
    recommended_uploads: list[str] = field(default_factory=list)
    burden_shift_triggered: bool = False
    burden_shift_flag: Optional[dict[str, Any]] = None
    reasoning_chain_flags: list[str] = field(default_factory=list)
    adverse_authority: list[dict[str, Any]] = field(default_factory=list)
    opposing_anticipation: list[str] = field(default_factory=list)
    element_report: str = ""  # full narrative ELEMENT blocks

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_id": self.test_id,
            "citation": self.citation,
            "source": self.source,
            "elements": [e.to_dict() for e in self.elements],
            "overall": self.overall.value,
            "citation_gate_ok": self.citation_gate_ok,
            "citation_flag": self.citation_flag,
            "gaps": list(self.gaps),
            "recommended_uploads": list(self.recommended_uploads),
            "burden_shift_triggered": self.burden_shift_triggered,
            "burden_shift_flag": self.burden_shift_flag,
            "reasoning_chain_flags": list(self.reasoning_chain_flags),
            "adverse_authority": list(self.adverse_authority),
            "opposing_anticipation": list(self.opposing_anticipation),
            "element_report": self.element_report,
        }

    def format_element_report(self) -> str:
        if self.element_report:
            return self.element_report
        blocks = [e.format_block() for e in self.elements]
        if self.burden_shift_triggered:
            blocks.append(
                "\nBURDEN SHIFT: Tenant has made out required elements for shift analysis.\n"
                "FLAG: BURDEN_SHIFT_TO_LANDLORD — landlord put to legitimate non-retaliatory cause.\n"
                "(Confirm on current RTA s. 56 and case law before filing.)"
            )
        return "\n\n".join(blocks)


# ---------------------------------------------------------------------------
# Canonical RTA s.56 retaliatory eviction scaffold (user-specified)
# ---------------------------------------------------------------------------


def rta_s56_retaliatory_eviction_test() -> LegalTest:
    """
    LEGAL_TEST id: RTA-s56-retaliatory-eviction

    Verify s. 56 text and case authorities on BC Laws / CanLII before filing.
    CIT-RTA-S56 is PARTIALLY_VERIFIED until exact_text is registered.
    """
    return LegalTest(
        test_id="RTA-s56-retaliatory-eviction",
        citation="RTA s.56(1)",
        citation_id="CIT-RTA-S56",
        jurisdiction="BC",
        source="Residential Tenancy Act, SBC 2002, c. 78, s. 56",
        short_name="Retaliatory eviction (RTA s.56)",
        applies_to=["retaliatory_eviction"],
        notes=(
            "s. 56 creates a presumption. If tenant proves E1 + E2 + E3, "
            "burden shifts to landlord to rebut by showing legitimate "
            "non-retaliatory cause. Engine should flag this burden shift "
            "in its reasoning chain."
        ),
        burden_shift=BurdenShiftRule(
            triggers_when_elements=[
                "E1-timely-dispute",
                "E2-prior-complaint",
                "E3-temporal-nexus",
            ],
            shifts_to="landlord",
            description=(
                "If tenant establishes timely dispute (E1), protected activity (E2), "
                "and temporal nexus (E3), a presumption / burden shift may arise: "
                "landlord must show legitimate non-retaliatory cause. "
                "Confirm current s. 56 wording and case law before relying."
            ),
            reasoning_flag="BURDEN_SHIFT_TO_LANDLORD",
        ),
        adverse_authority=[
            AdverseAuthorityNote(
                label="Preston v. May",
                parenthetical=(
                    "landlord can evict for legitimate cause even after tenant complaints "
                    "(illustrative label — VERIFY on CanLII; not in verified citation DB)"
                ),
            ),
            AdverseAuthorityNote(
                label="Yu v. Zhang",
                parenthetical=(
                    "temporal proximity alone insufficient without evidence of retaliatory intent "
                    "(illustrative label — VERIFY on CanLII; not in verified citation DB)"
                ),
            ),
        ],
        elements=[
            LegalTestElement(
                element_id="E1-timely-dispute",
                description="Tenant filed dispute within 15 days of receiving notice",
                evidence_type=ElementEvidenceType.PROCEDURAL,
                required=True,
                evidence=[
                    ElementEvidenceSpec(
                        role=ElementEvidenceRole.REQUIRED,
                        claim_tags=["retaliatory_eviction"],
                        fact_keys=["dispute_filed", "notice_received", "service_date"],
                        source_types=["GOVERNMENT_CORRESPONDENCE", "EMAIL", "OTHER"],
                        min_strength=0.4,
                        description=(
                            "RTB dispute filing receipt / portal confirmation dated within "
                            "15 days of notice service (confirm current RTB rules)."
                        ),
                    ),
                ],
            ),
            LegalTestElement(
                element_id="E2-prior-complaint",
                description=(
                    "Tenant engaged in protected activity (complained to landlord/RTB/"
                    "government body about habitability, repairs, or rights enforcement)"
                ),
                evidence_type=ElementEvidenceType.SUBSTANTIVE,
                required=True,
                protected_activities=[
                    "filing complaint with RTB",
                    "requesting repairs",
                    "asserting rights under RTA",
                    "contacting health/safety authority",
                    "complained to landlord about habitability, repairs, or rights",
                ],
                evidence=[
                    ElementEvidenceSpec(
                        role=ElementEvidenceRole.REQUIRED,
                        claim_tags=[
                            "retaliatory_eviction",
                            "non_repair",
                            "mold_hazard",
                            "city_enforcement",
                        ],
                        fact_keys=[
                            "protected_activity",
                            "repair_request",
                            "rtb_complaint",
                        ],
                        source_types=[
                            "EMAIL",
                            "TEXT_MESSAGE",
                            "GOVERNMENT_CORRESPONDENCE",
                        ],
                        min_strength=0.4,
                        description=(
                            "Complaint, repair request, or rights enforcement before the notice."
                        ),
                    ),
                ],
            ),
            LegalTestElement(
                element_id="E3-temporal-nexus",
                description=(
                    "Reasonable connection in timing between protected activity and eviction notice"
                ),
                evidence_type=ElementEvidenceType.INFERENTIAL,
                required=True,
                weight=0.30,
                evidence=[
                    ElementEvidenceSpec(
                        role=ElementEvidenceRole.REQUIRED,
                        claim_tags=["retaliatory_eviction"],
                        fact_keys=["sequence", "timing", "notice_to_end"],
                        source_types=["GOVERNMENT_CORRESPONDENCE", "PHOTO"],
                        min_strength=0.4,
                        description=(
                            "Timeline: protected activity then Notice to End Tenancy; "
                            "gap analysis informs strength of nexus."
                        ),
                    ),
                ],
                notes="Inferential — temporal proximity alone may be attacked (see adverse authority).",
            ),
            LegalTestElement(
                element_id="E4-absence-legitimate-cause",
                description=(
                    "Landlord's stated reasons are pretextual or insufficient on their own"
                ),
                evidence_type=ElementEvidenceType.INFERENTIAL,
                required=False,
                weight=0.40,
                evidence=[
                    ElementEvidenceSpec(
                        role=ElementEvidenceRole.SUPPORTING,
                        claim_tags=["retaliatory_eviction"],
                        description="Evidence undermining landlord's stated cause.",
                    ),
                    ElementEvidenceSpec(
                        role=ElementEvidenceRole.ADVERSE,
                        claim_tags=["rent_issue"],
                        description=(
                            "Proven independent legitimate cause (e.g. arrears) may "
                            "support landlord rebuttal after burden shift."
                        ),
                    ),
                ],
            ),
        ],
        verification_note=(
            "Scaffold only. Verify Residential Tenancy Act s. 56 on BC Laws "
            "(currency line) and every adverse case on CanLII before filing. "
            "GroundingGate refuses court-ready use of CIT-RTA-S56 until VERIFIED."
        ),
    )


# Back-compat aliases
def retaliatory_eviction_s56_test() -> LegalTest:
    return rta_s56_retaliatory_eviction_test()


def default_legal_tests() -> dict[str, LegalTest]:
    t = rta_s56_retaliatory_eviction_test()
    # both ids resolve to same test
    return {
        t.test_id: t,
        "TEST-RETALIATORY-EVICTION-S56": t,  # legacy alias
    }
