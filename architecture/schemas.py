"""
Core data contracts for BC Legal AI Associate.

These types are the foundation for matter isolation, provenance, and the
citation gate. They are not a database; persistence is a later backend step.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class Classification(str, Enum):
    FACT = "FACT"
    ALLEGATION = "ALLEGATION"
    LEGAL_ARGUMENT = "LEGAL_ARGUMENT"
    INFERENCE = "INFERENCE"
    ASSUMPTION = "ASSUMPTION"
    PROCEDURAL_HISTORY = "PROCEDURAL_HISTORY"
    RECOMMENDATION = "RECOMMENDATION"


class VerificationStatus(str, Enum):
    RECORD_SUPPORTED = "record-supported"
    PARTY_ALLEGED = "party-alleged"
    INFERRED = "inferred"
    UNVERIFIED = "unverified"
    DISPUTED = "disputed"


class AuthorityStatus(str, Enum):
    """Citation gate statuses — court-ready mode blocks UNVERIFIED."""

    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    REJECTED = "REJECTED"


class ApprovalAction(str, Enum):
    TREAT_AS_FACT = "treat_allegation_as_fact"
    ADD_AUTHORITY = "add_authority_to_filing"
    QUOTE_TRANSCRIPT = "quote_transcript"
    FINALIZE_DEADLINE = "finalize_deadline"
    MAKE_CONCESSION = "make_concession"
    REMOVE_GROUND = "remove_ground"
    WAIVE_PRIVILEGE = "waive_privilege"
    SIGNATURE_READY_AFFIDAVIT = "signature_ready_affidavit"
    SEND_CORRESPONDENCE = "send_correspondence"
    FILE_WITH_COURT = "file_with_court"


@dataclass
class Provenance:
    source_document: str
    page: Optional[int] = None
    paragraph: Optional[str] = None
    timestamp: Optional[str] = None  # e.g. transcript "00:04:36"
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    url: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Proposition:
    """Extracted claim with mandatory provenance and classification."""

    proposition: str
    classification: Classification
    source_document: str
    page: Optional[int] = None
    timestamp: Optional[str] = None
    confidence: float = 0.0
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["classification"] = self.classification.value
        d["verification_status"] = self.verification_status.value
        return d


@dataclass
class AuthorityRecord:
    """Retrieved or proposed legal authority with currency metadata."""

    official_title: str
    jurisdiction: str
    court_or_tribunal: Optional[str] = None
    neutral_citation: Optional[str] = None
    decision_date: Optional[str] = None
    effective_date: Optional[str] = None
    retrieval_date: Optional[str] = None
    paragraph_or_section: Optional[str] = None
    source_url: Optional[str] = None
    binding_or_persuasive: Optional[str] = None  # "binding" | "persuasive"
    remains_current: Optional[bool] = None
    subsequent_treatment: Optional[str] = None
    status: AuthorityStatus = AuthorityStatus.UNVERIFIED
    proposition_supported: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


def court_ready_allowed(authorities: list[AuthorityRecord]) -> tuple[bool, list[str]]:
    """Court-ready mode: refuse finalize if any authority is UNVERIFIED or REJECTED."""
    blockers: list[str] = []
    for a in authorities:
        if a.status in (AuthorityStatus.UNVERIFIED, AuthorityStatus.REJECTED):
            label = a.neutral_citation or a.official_title
            blockers.append(f"{a.status.value}: {label}")
    return (len(blockers) == 0, blockers)


@dataclass
class Matter:
    """Isolated legal matter workspace (schema only — no shared ambient state)."""

    title: str
    tribunal_or_court: Optional[str] = None
    file_numbers: list[str] = field(default_factory=list)
    parties: list[str] = field(default_factory=list)
    lawyers: list[str] = field(default_factory=list)
    pleadings: list[str] = field(default_factory=list)
    decisions_orders: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    witnesses: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    deadlines: list[str] = field(default_factory=list)
    legal_issues: list[str] = field(default_factory=list)
    authority_ids: list[str] = field(default_factory=list)
    remedies: list[str] = field(default_factory=list)
    draft_ids: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReviewReport:
    facts_checked: tuple[int, int] = (0, 0)
    unsupported_factual_statements: int = 0
    authorities_verified: tuple[int, int] = (0, 0)
    unverified_authorities: int = 0
    quotes_checked: tuple[int, int] = (0, 0)
    deadlines_checked: tuple[int, int] = (0, 0)
    cross_references_checked: tuple[int, int] = (0, 0)
    human_approval: str = "REQUIRED"

    def format(self) -> str:
        fc, ft = self.facts_checked
        av, at = self.authorities_verified
        qc, qt = self.quotes_checked
        dc, dt = self.deadlines_checked
        xc, xt = self.cross_references_checked
        return (
            f"Facts checked:                   {fc}/{ft}\n"
            f"Unsupported factual statements:  {self.unsupported_factual_statements}\n"
            f"Authorities verified:           {av}/{at}\n"
            f"Unverified authorities:         {self.unverified_authorities}\n"
            f"Quotes checked:                 {qc}/{qt}\n"
            f"Deadlines checked:              {dc}/{dt}\n"
            f"Cross-references checked:       {xc}/{xt}\n"
            f"Human approval:                 {self.human_approval}\n"
        )
