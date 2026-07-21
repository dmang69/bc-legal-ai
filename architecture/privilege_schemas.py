"""
Solicitor–client privilege domain model.

Privilege belongs to the client (privilege_owner = client_id), never the firm or AI.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class PrivilegeStatus(str, Enum):
    UNCLAIMED = "UNCLAIMED"
    CLAIMED = "CLAIMED"
    ASSERTED = "ASSERTED"
    UPHELD = "UPHELD"
    WAIVED = "WAIVED"
    PIERCED = "PIERCED"


class PrivilegeBasis(str, Enum):
    SOLICITOR_CLIENT = "solicitor_client"
    LITIGATION = "litigation"
    SETTLEMENT_IMPLIED = "settlement_implied"
    NONE = "none"


class PrincipalRole(str, Enum):
    CLIENT_PRINCIPAL = "client_principal"
    INSTRUCTING_LAWYER = "instructing_lawyer"
    ASSOCIATE_LAWYER = "associate_lawyer"
    PARALEGAL = "paralegal"
    AI_ASSOCIATE = "ai_associate"
    OPPOSING_COUNSEL = "opposing_counsel"
    TRIBUNAL_COURT = "tribunal_court"


class PartyCommRole(str, Enum):
    CLIENT = "client"
    LAWYER = "lawyer"
    THIRD_PARTY = "third_party"
    UNKNOWN = "unknown"


# States that block export without privilege review / lawyer sign-off
PROTECTED_FOR_EXPORT = frozenset(
    {
        PrivilegeStatus.CLAIMED,
        PrivilegeStatus.ASSERTED,
        PrivilegeStatus.UPHELD,
    }
)

# AI associate may read only these when explicitly task-scoped
AI_VISIBLE_PRIVILEGE = frozenset(
    {
        PrivilegeStatus.CLAIMED,
        PrivilegeStatus.ASSERTED,
        PrivilegeStatus.UPHELD,
    }
)

# Valid transitions: from -> allowed next states
PRIVILEGE_TRANSITIONS: dict[PrivilegeStatus, frozenset[PrivilegeStatus]] = {
    PrivilegeStatus.UNCLAIMED: frozenset(
        {PrivilegeStatus.CLAIMED, PrivilegeStatus.WAIVED, PrivilegeStatus.PIERCED}
    ),
    PrivilegeStatus.CLAIMED: frozenset(
        {
            PrivilegeStatus.ASSERTED,
            PrivilegeStatus.WAIVED,
            PrivilegeStatus.PIERCED,
            PrivilegeStatus.UPHELD,
        }
    ),
    PrivilegeStatus.ASSERTED: frozenset(
        {PrivilegeStatus.UPHELD, PrivilegeStatus.WAIVED, PrivilegeStatus.PIERCED}
    ),
    PrivilegeStatus.UPHELD: frozenset(
        {PrivilegeStatus.WAIVED, PrivilegeStatus.PIERCED}
    ),
    PrivilegeStatus.WAIVED: frozenset(),  # terminal for ordinary flow
    PrivilegeStatus.PIERCED: frozenset(),  # terminal
}


@dataclass
class WaiverEvent:
    actor_id: str
    basis: str
    scope: str
    timestamp: str = field(default_factory=_utcnow)
    auth_method: str = "explicit"
    notes: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PrivilegeMetadata:
    """Attached to every document / communication record."""

    privilege_owner: str  # client_id — never firm_id
    privilege_status: PrivilegeStatus = PrivilegeStatus.UNCLAIMED
    privilege_basis: PrivilegeBasis = PrivilegeBasis.NONE
    claim_date: Optional[str] = None
    asserted_in: Optional[str] = None  # proceeding_id
    waiver_events: list[WaiverEvent] = field(default_factory=list)
    classification_confidence: Optional[float] = None
    human_confirmed: bool = False
    jurisdiction: str = "BC"

    def to_dict(self) -> dict[str, Any]:
        return {
            "privilege_owner": self.privilege_owner,
            "privilege_status": self.privilege_status.value,
            "privilege_basis": self.privilege_basis.value,
            "claim_date": self.claim_date,
            "asserted_in": self.asserted_in,
            "waiver_events": [w.to_dict() for w in self.waiver_events],
            "classification_confidence": self.classification_confidence,
            "human_confirmed": self.human_confirmed,
            "jurisdiction": self.jurisdiction,
        }


@dataclass
class PrivilegeAuditEvent:
    actor_id: str
    action: str
    document_id: str
    matter_id: str
    timestamp: str = field(default_factory=_utcnow)
    ip_hash: Optional[str] = None
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    reason: Optional[str] = None
    auth_method: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MatterAccessGrant:
    """Per-user (or per AI task) access to a matter."""

    user_id: str
    matter_id: str
    role: PrincipalRole
    access_level: int = 1  # higher = more capability
    task_id: Optional[str] = None  # required for ai_associate scoping
    active: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["role"] = self.role.value
        return d


@dataclass
class PrivilegeTagProposal:
    """Output of Stage 1–2 classifier — not final until human_confirmed."""

    sender_role: PartyCommRole
    recipient_role: PartyCommRole
    advice_sought: bool
    advice_given: bool
    litigation_context: bool
    proposed_basis: PrivilegeBasis
    confidence: float
    requires_human_review: bool = False
    finalized: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "sender_role": self.sender_role.value,
            "recipient_role": self.recipient_role.value,
            "advice_sought": self.advice_sought,
            "advice_given": self.advice_given,
            "litigation_context": self.litigation_context,
            "proposed_basis": self.proposed_basis.value,
            "confidence": self.confidence,
            "requires_human_review": self.requires_human_review,
            "finalized": self.finalized,
        }


HUMAN_REVIEW_CONFIDENCE_THRESHOLD = 0.85
