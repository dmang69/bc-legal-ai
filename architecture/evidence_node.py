"""
EvidenceNode — graph-native evidence unit (ALA Layer 2).

Sequential node_id (EV-YYYY-NNNNNN) is immutable once assigned.
Maps to privilege Layer 0 tagging and hearing-readiness assessments.

Not legal advice. Authenticity / admissibility fields are assessments, not court findings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class SourceType(str, Enum):
    PHOTO = "PHOTO"
    EMAIL = "EMAIL"
    TEXT_MESSAGE = "TEXT_MESSAGE"
    RTB_DECISION = "RTB_DECISION"
    COURT_ORDER = "COURT_ORDER"
    INSPECTION_CERT = "INSPECTION_CERT"
    MEDICAL_RECORD = "MEDICAL_RECORD"
    LEASE_AGREEMENT = "LEASE_AGREEMENT"
    BANK_RECORD = "BANK_RECORD"
    WITNESS_STATEMENT = "WITNESS_STATEMENT"
    AUDIO_RECORDING = "AUDIO_RECORDING"
    VIDEO = "VIDEO"
    GOVERNMENT_CORRESPONDENCE = "GOVERNMENT_CORRESPONDENCE"
    NEWS_ARTICLE = "NEWS_ARTICLE"
    OTHER = "OTHER"


class PrivilegeClass(str, Enum):
    """Layer 0 privilege tagging at the node level."""

    OPEN = "OPEN"  # non-privileged / production-safe after normal review
    PROTECTED = "PROTECTED"  # claimed/asserted privilege — production gate required
    RESTRICTED = "RESTRICTED"  # elevated sensitivity (e.g. medical) even if not SC privilege
    WAIVED = "WAIVED"


class AuthenticityStatus(str, Enum):
    VERIFIED = "VERIFIED"
    DISPUTED = "DISPUTED"
    UNVERIFIED = "UNVERIFIED"


class BestEvidenceRule(str, Enum):
    ORIGINAL = "ORIGINAL"
    CERTIFIED_COPY = "CERTIFIED_COPY"
    PHOTOCOPY = "PHOTOCOPY"
    DIGITAL = "DIGITAL"


@dataclass
class KeyFact:
    """
    Discrete factual claim extractable from a node.

    fact_key: normalized claim identifier for pairwise intersection
    value: asserted value for that key (used to detect conflicts)
    fact: human-readable statement
    """

    fact: str
    confidence: float = 0.0
    source_span: Optional[str] = None
    fact_key: Optional[str] = None
    value: Optional[str] = None

    def resolved_key(self) -> str:
        if self.fact_key:
            return _norm_key(self.fact_key)
        return _norm_key(self.fact)

    def resolved_value(self) -> str:
        if self.value is not None and str(self.value).strip():
            return _norm_value(str(self.value))
        return _norm_value(self.fact)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact": self.fact,
            "confidence": self.confidence,
            "source_span": self.source_span,
            "fact_key": self.fact_key or self.resolved_key(),
            "value": self.value if self.value is not None else self.fact,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "KeyFact":
        return KeyFact(
            fact=str(data.get("fact") or ""),
            confidence=float(data.get("confidence") or 0.0),
            source_span=data.get("source_span"),
            fact_key=data.get("fact_key"),
            value=data.get("value"),
        )


def _norm_key(text: str) -> str:
    import re

    t = (text or "").lower().strip()
    t = re.sub(r"[^a-z0-9\s_\-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _norm_value(text: str) -> str:
    return _norm_key(text)


class ResolutionStrategy(str, Enum):
    A_PRIORITY = "A_PRIORITY"  # A has stronger authentication
    B_PRIORITY = "B_PRIORITY"
    NEEDS_HUMAN = "NEEDS_HUMAN"  # Can't auto-resolve
    BOTH_RELEVANT = "BOTH_RELEVANT"  # Different contexts/times


@dataclass
class ContradictionReport:
    fact: str  # fact_key
    node_a: str
    node_b: str
    node_a_claim: str
    node_b_claim: str
    resolution_strategy: ResolutionStrategy
    weight_difference: float
    node_a_confidence: float = 0.0
    node_b_confidence: float = 0.0
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact": self.fact,
            "node_a": self.node_a,
            "node_b": self.node_b,
            "node_a_claim": self.node_a_claim,
            "node_b_claim": self.node_b_claim,
            "resolution_strategy": self.resolution_strategy.value,
            "weight_difference": self.weight_difference,
            "node_a_confidence": self.node_a_confidence,
            "node_b_confidence": self.node_b_confidence,
            "note": self.note,
        }


@dataclass
class EntityMention:
    name: str
    role: str = "unknown"
    mention_count: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "mention_count": self.mention_count,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "EntityMention":
        return EntityMention(
            name=str(data.get("name") or ""),
            role=str(data.get("role") or "unknown"),
            mention_count=int(data.get("mention_count") or 1),
        )


@dataclass
class TemporalSequence:
    before: list[str] = field(default_factory=list)
    after: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"before": list(self.before), "after": list(self.after)}

    @staticmethod
    def from_dict(data: Optional[dict[str, Any]]) -> "TemporalSequence":
        if not data:
            return TemporalSequence()
        return TemporalSequence(
            before=list(data.get("before") or []),
            after=list(data.get("after") or []),
        )


@dataclass
class CustodySpan:
    holder: str
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    method: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "holder": self.holder,
            "from": self.from_date,
            "to": self.to_date,
            "method": self.method,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "CustodySpan":
        return CustodySpan(
            holder=str(data.get("holder") or "unknown"),
            from_date=data.get("from") or data.get("from_date"),
            to_date=data.get("to") or data.get("to_date"),
            method=str(data.get("method") or "unknown"),
        )


@dataclass
class AlterationEvent:
    timestamp: str
    actor: str
    description: str
    prior_hash: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "actor": self.actor,
            "description": self.description,
            "prior_hash": self.prior_hash,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "AlterationEvent":
        return AlterationEvent(
            timestamp=str(data.get("timestamp") or ""),
            actor=str(data.get("actor") or ""),
            description=str(data.get("description") or ""),
            prior_hash=data.get("prior_hash"),
        )


@dataclass
class AdmissibilityAssessment:
    likely_admissible: bool = False
    grounds: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    foundation_witness: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "likely_admissible": self.likely_admissible,
            "grounds": list(self.grounds),
            "risks": list(self.risks),
            "foundation_witness": self.foundation_witness,
        }

    @staticmethod
    def from_dict(data: Optional[dict[str, Any]]) -> "AdmissibilityAssessment":
        if not data:
            return AdmissibilityAssessment()
        return AdmissibilityAssessment(
            likely_admissible=bool(data.get("likely_admissible", False)),
            grounds=list(data.get("grounds") or []),
            risks=list(data.get("risks") or []),
            foundation_witness=data.get("foundation_witness"),
        )


@dataclass
class EvidenceNode:
    """
    Full graph evidence node.

    node_id is sequential and immutable (EV-YYYY-NNNNNN).
    doc_hash is sha256 of source bytes (prefixed sha256: when serialized).
    """

    node_id: str
    doc_hash: str  # "sha256:hex" or bare hex
    privilege_class: PrivilegeClass = PrivilegeClass.OPEN
    source_type: SourceType = SourceType.OTHER
    date_created: Optional[str] = None
    date_received: Optional[str] = None
    date_entered_system: str = field(default_factory=_utcnow)
    custodian: str = "unknown"
    authenticity_status: AuthenticityStatus = AuthenticityStatus.UNVERIFIED
    hearsay_flag: bool = False
    hearsay_exception: Optional[str] = None
    best_evidence_rule: BestEvidenceRule = BestEvidenceRule.DIGITAL
    extracted_text: str = ""
    key_facts: list[KeyFact] = field(default_factory=list)
    entities_mentioned: list[EntityMention] = field(default_factory=list)
    corroborates: list[str] = field(default_factory=list)
    contradicts: list[str] = field(default_factory=list)
    causally_linked_to: list[str] = field(default_factory=list)
    temporal_sequence: TemporalSequence = field(default_factory=TemporalSequence)
    chain_of_custody: list[CustodySpan] = field(default_factory=list)
    alteration_history: list[AlterationEvent] = field(default_factory=list)
    exhibit_number: Optional[str] = None
    admissibility_assessment: AdmissibilityAssessment = field(
        default_factory=AdmissibilityAssessment
    )
    # matter partition + optional link back to matrix row UUID
    matter_id: Optional[str] = None
    source_file: Optional[str] = None
    matrix_evidence_id: Optional[str] = None
    claim_tags: list[str] = field(default_factory=list)
    contradiction_warning: bool = False
    contradiction_fact_keys: list[str] = field(default_factory=list)

    def bare_hash(self) -> str:
        h = self.doc_hash
        if h.startswith("sha256:"):
            return h[7:]
        return h

    def requires_privilege_gate(self) -> bool:
        return self.privilege_class in (
            PrivilegeClass.PROTECTED,
            PrivilegeClass.RESTRICTED,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "doc_hash": self.doc_hash
            if self.doc_hash.startswith("sha256:")
            else f"sha256:{self.doc_hash}",
            "privilege_class": self.privilege_class.value,
            "source_type": self.source_type.value,
            "date_created": self.date_created,
            "date_received": self.date_received,
            "date_entered_system": self.date_entered_system,
            "custodian": self.custodian,
            "authenticity_status": self.authenticity_status.value,
            "hearsay_flag": self.hearsay_flag,
            "hearsay_exception": self.hearsay_exception,
            "best_evidence_rule": self.best_evidence_rule.value,
            "extracted_text": self.extracted_text,
            "key_facts": [k.to_dict() for k in self.key_facts],
            "entities_mentioned": [e.to_dict() for e in self.entities_mentioned],
            "corroborates": list(self.corroborates),
            "contradicts": list(self.contradicts),
            "causally_linked_to": list(self.causally_linked_to),
            "temporal_sequence": self.temporal_sequence.to_dict(),
            "chain_of_custody": [c.to_dict() for c in self.chain_of_custody],
            "alteration_history": [a.to_dict() for a in self.alteration_history],
            "exhibit_number": self.exhibit_number,
            "admissibility_assessment": self.admissibility_assessment.to_dict(),
            "matter_id": self.matter_id,
            "source_file": self.source_file,
            "matrix_evidence_id": self.matrix_evidence_id,
            "claim_tags": list(self.claim_tags),
            "contradiction_warning": self.contradiction_warning,
            "contradiction_fact_keys": list(self.contradiction_fact_keys),
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "EvidenceNode":
        return EvidenceNode(
            node_id=str(data["node_id"]),
            doc_hash=str(data.get("doc_hash") or ""),
            privilege_class=PrivilegeClass(
                data.get("privilege_class", PrivilegeClass.OPEN.value)
            ),
            source_type=SourceType(data.get("source_type", SourceType.OTHER.value)),
            date_created=data.get("date_created"),
            date_received=data.get("date_received"),
            date_entered_system=data.get("date_entered_system") or _utcnow(),
            custodian=str(data.get("custodian") or "unknown"),
            authenticity_status=AuthenticityStatus(
                data.get("authenticity_status", AuthenticityStatus.UNVERIFIED.value)
            ),
            hearsay_flag=bool(data.get("hearsay_flag", False)),
            hearsay_exception=data.get("hearsay_exception"),
            best_evidence_rule=BestEvidenceRule(
                data.get("best_evidence_rule", BestEvidenceRule.DIGITAL.value)
            ),
            extracted_text=str(data.get("extracted_text") or ""),
            key_facts=[KeyFact.from_dict(x) for x in (data.get("key_facts") or [])],
            entities_mentioned=[
                EntityMention.from_dict(x) for x in (data.get("entities_mentioned") or [])
            ],
            corroborates=list(data.get("corroborates") or []),
            contradicts=list(data.get("contradicts") or []),
            causally_linked_to=list(data.get("causally_linked_to") or []),
            temporal_sequence=TemporalSequence.from_dict(data.get("temporal_sequence")),
            chain_of_custody=[
                CustodySpan.from_dict(x) for x in (data.get("chain_of_custody") or [])
            ],
            alteration_history=[
                AlterationEvent.from_dict(x) for x in (data.get("alteration_history") or [])
            ],
            exhibit_number=data.get("exhibit_number"),
            admissibility_assessment=AdmissibilityAssessment.from_dict(
                data.get("admissibility_assessment")
            ),
            matter_id=data.get("matter_id"),
            source_file=data.get("source_file"),
            matrix_evidence_id=data.get("matrix_evidence_id"),
            claim_tags=list(data.get("claim_tags") or []),
            contradiction_warning=bool(data.get("contradiction_warning", False)),
            contradiction_fact_keys=list(data.get("contradiction_fact_keys") or []),
        )


# Map flat matrix EvidenceType → SourceType
_MATRIX_TYPE_MAP = {
    "photo": SourceType.PHOTO,
    "contract": SourceType.LEASE_AGREEMENT,
    "notice": SourceType.GOVERNMENT_CORRESPONDENCE,
    "correspondence": SourceType.EMAIL,
    "official_order": SourceType.RTB_DECISION,
    "financial": SourceType.BANK_RECORD,
    "transcript": SourceType.WITNESS_STATEMENT,
    "audio": SourceType.AUDIO_RECORDING,
    "video_frame": SourceType.VIDEO,
    "other": SourceType.OTHER,
}


def source_type_from_matrix(evidence_type_value: str) -> SourceType:
    return _MATRIX_TYPE_MAP.get(evidence_type_value, SourceType.OTHER)


def privilege_class_from_item(
    privilege_lock: bool,
    privilege_state_value: str,
) -> PrivilegeClass:
    if privilege_state_value == "WAIVED":
        return PrivilegeClass.WAIVED
    if privilege_lock or privilege_state_value in ("CLAIMED", "ASSERTED", "UPHELD"):
        return PrivilegeClass.PROTECTED
    return PrivilegeClass.OPEN


def evidence_item_to_node(
    item: Any,
    *,
    node_id: str,
    extracted_text: str = "",
    custodian: str = "unknown",
) -> EvidenceNode:
    """Promote a matrix EvidenceItem into an EvidenceNode (graph layer)."""
    from architecture.schemas import EvidenceItem

    if not isinstance(item, EvidenceItem):
        raise TypeError("expected EvidenceItem")

    h = item.file_hash or ""
    doc_hash = h if h.startswith("sha256:") else (f"sha256:{h}" if h else f"sha256:unknown-{uuid4().hex[:8]}")

    custody_spans: list[CustodySpan] = []
    for ev in item.chain_of_custody or []:
        if isinstance(ev, dict) and "holder" in ev:
            custody_spans.append(CustodySpan.from_dict(ev))
        elif isinstance(ev, dict):
            custody_spans.append(
                CustodySpan(
                    holder=str(ev.get("actor_id") or custodian),
                    from_date=ev.get("timestamp"),
                    to_date="present",
                    method=str(ev.get("action") or "system_event"),
                )
            )

    adm = AdmissibilityAssessment(
        likely_admissible=item.admissibility_flag.value == "likely_admissible",
        grounds=[],
        risks=["needs_verification"]
        if item.admissibility_flag.value == "needs_verification"
        else [],
        foundation_witness=custodian if custodian != "unknown" else None,
    )

    return EvidenceNode(
        node_id=node_id,
        doc_hash=doc_hash,
        privilege_class=privilege_class_from_item(
            item.privilege_lock, item.privilege_state.value
        ),
        source_type=source_type_from_matrix(item.evidence_type.value),
        date_created=item.date_captured,
        date_received=item.date_received,
        date_entered_system=_utcnow(),
        custodian=custodian,
        authenticity_status=AuthenticityStatus.UNVERIFIED,
        best_evidence_rule=BestEvidenceRule.DIGITAL,
        extracted_text=extracted_text or item.human_notes,
        key_facts=[],
        entities_mentioned=[],
        corroborates=list(item.corroborates),  # may be UUID; re-link later to node_ids
        contradicts=list(item.contradicts),
        matter_id=item.matter_id,
        source_file=item.source_file,
        matrix_evidence_id=item.evidence_id,
        claim_tags=list(item.claim_tags),
        chain_of_custody=custody_spans
        or [
            CustodySpan(
                holder=custodian,
                from_date=item.date_captured or item.date_received,
                to_date="present",
                method="system_ingest",
            )
        ],
        admissibility_assessment=adm,
    )
