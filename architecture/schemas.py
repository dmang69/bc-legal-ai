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

from architecture.privilege_schemas import PrivilegeBasis, PrivilegeStatus


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


# --- Layer 2: Evidence Matrix (ALA) ---


class EvidenceType(str, Enum):
    PHOTO = "photo"
    CONTRACT = "contract"
    NOTICE = "notice"
    CORRESPONDENCE = "correspondence"
    OFFICIAL_ORDER = "official_order"
    FINANCIAL = "financial"
    TRANSCRIPT = "transcript"
    AUDIO = "audio"
    VIDEO_FRAME = "video_frame"
    OTHER = "other"


class AdmissibilityFlag(str, Enum):
    LIKELY_ADMISSIBLE = "likely_admissible"
    QUESTIONABLE = "questionable"
    INADMISSIBLE = "inadmissible"
    NEEDS_VERIFICATION = "needs_verification"


class DocTrack(str, Enum):
    """Layer 1 classifier routes."""

    CONTRACT_LEASE = "contract_lease"
    GOVERNMENT_FORM_NOTICE = "government_form_notice"
    PHOTOGRAPH = "photograph"
    EMAIL_CORRESPONDENCE = "email_correspondence"
    FINANCIAL_RECORD = "financial_record"
    LEGAL_DECISION_ORDER = "legal_decision_order"
    MISCELLANEOUS = "miscellaneous"


@dataclass
class CustodyEvent:
    """Append-only chain-of-custody entry (jsonb array element)."""

    action: str
    actor_id: str = "system"
    timestamp: Optional[str] = None
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "actor_id": self.actor_id,
            "timestamp": self.timestamp,
            "detail": self.detail,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "CustodyEvent":
        return CustodyEvent(
            action=str(data.get("action") or "unknown"),
            actor_id=str(data.get("actor_id") or "system"),
            timestamp=data.get("timestamp"),
            detail=str(data.get("detail") or ""),
        )


@dataclass
class EvidenceItem:
    """
    Evidence matrix row — canonical field set for matter-partitioned evidence.

    evidence_id is immutable; matter_id is the privilege/access partition key.
    privilege_lock=True blocks export without the privilege production gate.
    """

    source_file: str
    matter_id: Optional[str] = None
    evidence_type: EvidenceType = EvidenceType.OTHER
    file_hash: Optional[str] = None  # SHA-256 of original bytes
    privilege_state: PrivilegeStatus = PrivilegeStatus.UNCLAIMED
    privilege_basis: PrivilegeBasis = PrivilegeBasis.NONE
    privilege_lock: bool = False
    date_captured: Optional[str] = None
    date_received: Optional[str] = None
    parties_referenced: list[str] = field(default_factory=list)
    location_referenced: Optional[str] = None
    claim_tags: list[str] = field(default_factory=list)
    contradicts: list[str] = field(default_factory=list)
    corroborates: list[str] = field(default_factory=list)
    hearing_relevance: float = 0.0
    admissibility_flag: AdmissibilityFlag = AdmissibilityFlag.NEEDS_VERIFICATION
    ocr_confidence: float = 0.0
    human_notes: str = ""
    chain_of_custody: list[dict[str, Any]] = field(default_factory=list)
    page_count: Optional[int] = None
    evidence_id: str = field(default_factory=lambda: str(uuid4()))

    # --- backward-compat aliases ---
    @property
    def id(self) -> str:
        return self.evidence_id

    @id.setter
    def id(self, value: str) -> None:
        self.evidence_id = value

    @property
    def content_sha256(self) -> Optional[str]:
        return self.file_hash

    @content_sha256.setter
    def content_sha256(self, value: Optional[str]) -> None:
        self.file_hash = value

    def append_custody(
        self,
        action: str,
        *,
        actor_id: str = "system",
        detail: str = "",
        timestamp: Optional[str] = None,
    ) -> None:
        from datetime import datetime, timezone

        ts = timestamp or datetime.now(timezone.utc).isoformat()
        self.chain_of_custody.append(
            CustodyEvent(
                action=action, actor_id=actor_id, timestamp=ts, detail=detail
            ).to_dict()
        )

    def requires_privilege_gate(self) -> bool:
        """Export blocked if lock set or protected privilege state."""
        if self.privilege_lock:
            return True
        return self.privilege_state in (
            PrivilegeStatus.CLAIMED,
            PrivilegeStatus.ASSERTED,
            PrivilegeStatus.UPHELD,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "matter_id": self.matter_id,
            "source_file": self.source_file,
            "file_hash": self.file_hash,
            "privilege_state": self.privilege_state.value,
            "privilege_basis": self.privilege_basis.value,
            "privilege_lock": self.privilege_lock,
            "evidence_type": self.evidence_type.value,
            "date_captured": self.date_captured,
            "date_received": self.date_received,
            "parties_referenced": list(self.parties_referenced),
            "location_referenced": self.location_referenced,
            "claim_tags": list(self.claim_tags),
            "contradicts": list(self.contradicts),
            "corroborates": list(self.corroborates),
            "hearing_relevance": self.hearing_relevance,
            "admissibility_flag": self.admissibility_flag.value,
            "ocr_confidence": self.ocr_confidence,
            "human_notes": self.human_notes,
            "chain_of_custody": list(self.chain_of_custody),
            "page_count": self.page_count,
            # legacy keys for older JSONL
            "id": self.evidence_id,
            "content_sha256": self.file_hash,
        }


@dataclass
class IngestedDocument:
    """Layer 1 output: original preserved + derived text layer."""

    source_file: str
    track: DocTrack
    raw_text: str
    normalized_fields: dict[str, Any] = field(default_factory=dict)
    thumbnail_path: Optional[str] = None
    ocr_confidence: float = 0.0
    content_sha256: Optional[str] = None
    matter_id: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["track"] = self.track.value
        return d


# --- Layer 4: Argument builder ---


@dataclass
class StatuteRef:
    """Must be verified against BC Laws (or other official source) before court-ready use."""

    short_cite: str
    section: Optional[str] = None
    source_url: Optional[str] = None
    status: AuthorityStatus = AuthorityStatus.UNVERIFIED

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class EvidenceRef:
    evidence_id: str
    note: Optional[str] = None
    page: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Counterargument:
    defense: str
    rebuttal_evidence_ids: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Remedy:
    description: str
    legal_basis: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LegalArgument:
    """Syllogistic argument package — factual predicates only via evidence IDs."""

    claim: str
    legal_basis: list[StatuteRef] = field(default_factory=list)
    factual_predicate: list[EvidenceRef] = field(default_factory=list)
    burden_of_proof: str = "balance of probabilities"
    opposing_arguments: list[Counterargument] = field(default_factory=list)
    remedies_sought: list[Remedy] = field(default_factory=list)
    confidence: float = 0.0
    evidence_gaps: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))

    def ungrounded(self) -> bool:
        return len(self.factual_predicate) == 0 and len(self.legal_basis) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "claim": self.claim,
            "legal_basis": [x.to_dict() for x in self.legal_basis],
            "factual_predicate": [x.to_dict() for x in self.factual_predicate],
            "burden_of_proof": self.burden_of_proof,
            "opposing_arguments": [x.to_dict() for x in self.opposing_arguments],
            "remedies_sought": [x.to_dict() for x in self.remedies_sought],
            "confidence": self.confidence,
            "evidence_gaps": list(self.evidence_gaps),
            "insufficient_evidence": self.ungrounded(),
        }


INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
