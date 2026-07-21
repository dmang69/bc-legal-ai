"""
GroundingGate contracts — every system claim must bind evidence + law + inference.

Refuse output if any required element is missing or broken.
Not legal advice; gate is a safety mechanism for workbench outputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from architecture.schemas import AuthorityStatus


class GroundingRefusalReason(str, Enum):
    MISSING_FACTUAL_BASIS = "MISSING_FACTUAL_BASIS"
    MISSING_LEGAL_BASIS = "MISSING_LEGAL_BASIS"
    BROKEN_INFERENCE_CHAIN = "BROKEN_INFERENCE_CHAIN"
    UNVERIFIED_CITATION = "UNVERIFIED_CITATION"
    REJECTED_CITATION = "REJECTED_CITATION"
    EMPTY_CLAIM = "EMPTY_CLAIM"


REFUSAL_MESSAGES = {
    GroundingRefusalReason.MISSING_FACTUAL_BASIS: (
        "No evidence supports this claim. Add evidence or revise query."
    ),
    GroundingRefusalReason.MISSING_LEGAL_BASIS: (
        "No legal authority found. Search knowledge base or flag for human."
    ),
    GroundingRefusalReason.BROKEN_INFERENCE_CHAIN: (
        "Logical gap between evidence and conclusion. Review inference steps."
    ),
    GroundingRefusalReason.UNVERIFIED_CITATION: (
        "Legal authority is UNVERIFIED. Verify citation or flag for human."
    ),
    GroundingRefusalReason.REJECTED_CITATION: (
        "Legal authority is REJECTED. Remove or replace the citation."
    ),
    GroundingRefusalReason.EMPTY_CLAIM: (
        "Empty claim. Provide a proposition to ground."
    ),
}


@dataclass
class Citation:
    """Legal authority reference for grounding (must resolve in verified citation DB)."""

    short_cite: str
    citation_id: Optional[str] = None
    neutral_citation: Optional[str] = None
    section: Optional[str] = None
    source_url: Optional[str] = None
    status: AuthorityStatus = AuthorityStatus.UNVERIFIED
    official_title: Optional[str] = None
    jurisdiction: str = "BC"

    def to_dict(self) -> dict[str, Any]:
        return {
            "citation_id": self.citation_id,
            "short_cite": self.short_cite,
            "neutral_citation": self.neutral_citation,
            "section": self.section,
            "source_url": self.source_url,
            "status": self.status.value,
            "official_title": self.official_title,
            "jurisdiction": self.jurisdiction,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Citation":
        st = data.get("status", AuthorityStatus.UNVERIFIED.value)
        return Citation(
            short_cite=str(data.get("short_cite") or data.get("official_title") or ""),
            citation_id=data.get("citation_id"),
            neutral_citation=data.get("neutral_citation"),
            section=data.get("section"),
            source_url=data.get("source_url"),
            status=AuthorityStatus(st) if not isinstance(st, AuthorityStatus) else st,
            official_title=data.get("official_title"),
            jurisdiction=str(data.get("jurisdiction") or "BC"),
        )


@dataclass
class InferenceStep:
    """One explicit logical step connecting evidence to conclusion."""

    statement: str
    premise_type: str = "inference"  # fact | law | inference | conclusion
    supports_from: list[str] = field(default_factory=list)  # node_ids or citation_ids
    step_id: str = field(default_factory=lambda: str(uuid4())[:8])

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "statement": self.statement,
            "premise_type": self.premise_type,
            "supports_from": list(self.supports_from),
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "InferenceStep":
        return InferenceStep(
            statement=str(data.get("statement") or ""),
            premise_type=str(data.get("premise_type") or "inference"),
            supports_from=list(data.get("supports_from") or []),
            step_id=str(data.get("step_id") or str(uuid4())[:8]),
        )


@dataclass
class GroundedClaim:
    """A claim offered for GroundingGate evaluation."""

    claim: str
    factual_basis: Optional[str] = None  # EvidenceNode.node_id
    legal_basis: Optional[Citation] = None
    inference_chain: list[InferenceStep] = field(default_factory=list)
    claim_id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim": self.claim,
            "factual_basis": self.factual_basis,
            "legal_basis": self.legal_basis.to_dict() if self.legal_basis else None,
            "inference_chain": [s.to_dict() for s in self.inference_chain],
        }


@dataclass
class GroundingResult:
    allowed: bool
    claim: str
    reasons: list[GroundingRefusalReason] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    grounded: Optional[GroundedClaim] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "claim": self.claim,
            "reasons": [r.value for r in self.reasons],
            "messages": list(self.messages),
            "grounded": self.grounded.to_dict() if self.grounded else None,
        }

    def refuse_text(self) -> str:
        if self.allowed:
            return ""
        return "REFUSE_OUTPUT\n" + "\n".join(f"- {m}" for m in self.messages)
