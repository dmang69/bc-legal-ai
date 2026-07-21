"""
LegalTest — structured multi-element legal tests for argument assembly.

Elements require evidence mapping; statutory pins must resolve in CitationDB.
Not legal advice. Element lists are workbench scaffolds — re-verify on BC Laws.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ElementEvidenceRole(str, Enum):
    REQUIRED = "REQUIRED"  # must have supporting evidence to mark element satisfied
    SUPPORTING = "SUPPORTING"  # helpful but not load-bearing alone
    ADVERSE = "ADVERSE"  # if present, may defeat or weaken the element


class ElementStatus(str, Enum):
    SATISFIED = "SATISFIED"
    PARTIAL = "PARTIAL"
    NOT_SATISFIED = "NOT_SATISFIED"
    UNKNOWN = "UNKNOWN"


@dataclass
class ElementEvidenceSpec:
    """What kind of evidence can satisfy an element."""

    role: ElementEvidenceRole = ElementEvidenceRole.REQUIRED
    claim_tags: list[str] = field(default_factory=list)
    fact_keys: list[str] = field(default_factory=list)
    source_types: list[str] = field(default_factory=list)  # EvidenceNode SourceType values
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
            role=ElementEvidenceRole(role) if not isinstance(role, ElementEvidenceRole) else role,
            claim_tags=list(data.get("claim_tags") or []),
            fact_keys=list(data.get("fact_keys") or []),
            source_types=list(data.get("source_types") or []),
            min_strength=float(data.get("min_strength") or 0.4),
            description=str(data.get("description") or ""),
        )


@dataclass
class LegalTestElement:
    element_id: str
    description: str
    protected_activities: list[str] = field(default_factory=list)
    evidence: list[ElementEvidenceSpec] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "element_id": self.element_id,
            "description": self.description,
            "protected_activities": list(self.protected_activities),
            "evidence": [e.to_dict() for e in self.evidence],
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "LegalTestElement":
        return LegalTestElement(
            element_id=str(data.get("element_id") or ""),
            description=str(data.get("description") or ""),
            protected_activities=list(data.get("protected_activities") or []),
            evidence=[
                ElementEvidenceSpec.from_dict(x) for x in (data.get("evidence") or [])
            ],
            notes=str(data.get("notes") or ""),
        )


@dataclass
class LegalTest:
    """
    Multi-element legal test scaffold.

    citation must be verified in CitationDB before court-ready use of the test.
    """

    test_id: str
    citation: str  # e.g. "RTA s.56(1)"
    elements: list[LegalTestElement] = field(default_factory=list)
    short_name: str = ""
    jurisdiction: str = "BC"
    applies_to: list[str] = field(default_factory=list)
    citation_id: Optional[str] = None  # e.g. CIT-RTA-S56
    burden: str = "balance of probabilities"
    verification_note: str = (
        "Legal test scaffold for workbench analysis. Verify every statutory pin "
        "and element wording on BC Laws / CanLII before filing. Not legal advice."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_id": self.test_id,
            "citation": self.citation,
            "citation_id": self.citation_id,
            "short_name": self.short_name or self.test_id,
            "jurisdiction": self.jurisdiction,
            "applies_to": list(self.applies_to),
            "burden": self.burden,
            "elements": [e.to_dict() for e in self.elements],
            "verification_note": self.verification_note,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "LegalTest":
        return LegalTest(
            test_id=str(data.get("test_id") or ""),
            citation=str(data.get("citation") or ""),
            elements=[
                LegalTestElement.from_dict(x) for x in (data.get("elements") or [])
            ],
            short_name=str(data.get("short_name") or ""),
            jurisdiction=str(data.get("jurisdiction") or "BC"),
            applies_to=list(data.get("applies_to") or []),
            citation_id=data.get("citation_id"),
            burden=str(data.get("burden") or "balance of probabilities"),
            verification_note=str(
                data.get("verification_note")
                or LegalTest(test_id="", citation="").verification_note
            ),
        )


@dataclass
class ElementEvaluation:
    element_id: str
    status: ElementStatus
    matching_node_ids: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "element_id": self.element_id,
            "status": self.status.value,
            "matching_node_ids": list(self.matching_node_ids),
            "missing_evidence": list(self.missing_evidence),
            "notes": self.notes,
        }


@dataclass
class LegalTestEvaluation:
    test_id: str
    citation: str
    elements: list[ElementEvaluation] = field(default_factory=list)
    overall: ElementStatus = ElementStatus.UNKNOWN
    citation_gate_ok: bool = False
    citation_flag: Optional[dict[str, Any]] = None
    gaps: list[dict[str, Any]] = field(default_factory=list)
    recommended_uploads: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_id": self.test_id,
            "citation": self.citation,
            "elements": [e.to_dict() for e in self.elements],
            "overall": self.overall.value,
            "citation_gate_ok": self.citation_gate_ok,
            "citation_flag": self.citation_flag,
            "gaps": list(self.gaps),
            "recommended_uploads": list(self.recommended_uploads),
        }


def retaliatory_eviction_s56_test() -> LegalTest:
    """
    Scaffold for retaliatory-eviction style analysis under RTA s.56 reference.

    IMPORTANT: Element wording and pin are workbench structure only.
    CIT-RTA-S56 is PARTIALLY_VERIFIED in the citation DB until full BC Laws check.
    Re-verify section number, subsections, and elements before any filing.
    """
    return LegalTest(
        test_id="TEST-RETALIATORY-EVICTION-S56",
        citation="RTA s.56(1)",
        citation_id="CIT-RTA-S56",
        short_name="Retaliatory eviction (RTA s.56 scaffold)",
        applies_to=["retaliatory_eviction"],
        elements=[
            LegalTestElement(
                element_id="ELEMENT-1",
                description="Tenant engaged in protected activity",
                protected_activities=[
                    "filing complaint with RTB",
                    "requesting repairs",
                    "asserting rights under RTA",
                    "contacting health/safety authority",
                ],
                evidence=[
                    ElementEvidenceSpec(
                        role=ElementEvidenceRole.REQUIRED,
                        claim_tags=["retaliatory_eviction", "non_repair", "mold_hazard"],
                        fact_keys=["protected_activity", "repair_request", "rtb_complaint"],
                        source_types=["EMAIL", "TEXT_MESSAGE", "GOVERNMENT_CORRESPONDENCE"],
                        min_strength=0.4,
                        description=(
                            "Communications or filings showing complaint, repair request, "
                            "or other protected activity before the notice."
                        ),
                    ),
                ],
            ),
            LegalTestElement(
                element_id="ELEMENT-2",
                description="Landlord knew (or reasonably should have known) of the protected activity",
                evidence=[
                    ElementEvidenceSpec(
                        role=ElementEvidenceRole.REQUIRED,
                        claim_tags=["retaliatory_eviction", "non_repair"],
                        fact_keys=["landlord_notice", "service_of_complaint"],
                        min_strength=0.4,
                        description="Proof of delivery / receipt / contemporaneous response by landlord.",
                    ),
                ],
            ),
            LegalTestElement(
                element_id="ELEMENT-3",
                description="Landlord took step to end tenancy (or threaten to end tenancy)",
                evidence=[
                    ElementEvidenceSpec(
                        role=ElementEvidenceRole.REQUIRED,
                        claim_tags=["retaliatory_eviction"],
                        fact_keys=["notice_to_end", "eviction_notice"],
                        source_types=["GOVERNMENT_CORRESPONDENCE", "PHOTO"],
                        min_strength=0.5,
                        description="Notice to End Tenancy or equivalent step to terminate.",
                    ),
                ],
            ),
            LegalTestElement(
                element_id="ELEMENT-4",
                description="Temporal / causal link — step followed protected activity in circumstances supporting retaliation inference",
                evidence=[
                    ElementEvidenceSpec(
                        role=ElementEvidenceRole.REQUIRED,
                        claim_tags=["retaliatory_eviction"],
                        fact_keys=["sequence", "timing"],
                        min_strength=0.4,
                        description=(
                            "Timeline showing proximity of protected activity to notice; "
                            "gap analysis may strengthen or weaken inference."
                        ),
                    ),
                    ElementEvidenceSpec(
                        role=ElementEvidenceRole.ADVERSE,
                        claim_tags=["rent_issue"],
                        description="Independent legitimate grounds (e.g. proven arrears) may defeat retaliation inference.",
                    ),
                ],
                notes="Causal inference is fact-sensitive; opposing will offer alternate justification.",
            ),
        ],
        verification_note=(
            "Scaffold only. Verify RTA s.56 text, subsections, and current elements on "
            "BC Laws before relying. GroundingGate will refuse court-ready use until "
            "CIT-RTA-S56 is VERIFIED with official exact_text."
        ),
    )


def default_legal_tests() -> dict[str, LegalTest]:
    t = retaliatory_eviction_s56_test()
    return {t.test_id: t}
