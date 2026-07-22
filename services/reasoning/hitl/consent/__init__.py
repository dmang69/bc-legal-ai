"""HITL A — Client consent capture & tracking."""

from services.reasoning.hitl.consent.audit import ConsentAuditEntry, ConsentAuditLog
from services.reasoning.hitl.consent.ledger import ConsentLedger, ConsentRecord, WithdrawalPlan
from services.reasoning.hitl.consent.privilege_bridge import (
    ConsentGateResult,
    consent_allows_privilege_class,
)
from services.reasoning.hitl.consent.scopes import (
    PLAIN_LANGUAGE,
    TENANCY_FACTS,
    ConsentScope,
    ConsentStatus,
    plain_language_for,
)
from services.reasoning.hitl.schemas.common import ConsentGateBlocked

__all__ = [
    "ConsentAuditLog",
    "ConsentAuditEntry",
    "ConsentLedger",
    "ConsentRecord",
    "WithdrawalPlan",
    "ConsentScope",
    "ConsentStatus",
    "TENANCY_FACTS",
    "PLAIN_LANGUAGE",
    "plain_language_for",
    "ConsentGateResult",
    "consent_allows_privilege_class",
    "ConsentGateBlocked",
]
