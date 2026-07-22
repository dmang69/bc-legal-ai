"""Consent gates privilege *boundaries* for processing — not waiver."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from architecture.evidence_node import PrivilegeClass, SourceType
from services.reasoning.hitl.consent.ledger import ConsentLedger
from services.reasoning.hitl.consent.scopes import ConsentScope


PRIVILEGE_CONSENT_MAP: dict[PrivilegeClass, list[ConsentScope]] = {
    PrivilegeClass.OPEN: [ConsentScope.AI_ANALYSIS],
    PrivilegeClass.PROTECTED: [
        ConsentScope.AI_ANALYSIS,
        ConsentScope.DISCLOSE_TO_COUNSEL,
    ],
    PrivilegeClass.RESTRICTED: [
        ConsentScope.AI_ANALYSIS,
        ConsentScope.DISCLOSE_TO_COUNSEL,
        ConsentScope.MEDICAL_INFORMATION,
    ],
    PrivilegeClass.WAIVED: [ConsentScope.AI_ANALYSIS],
}

SOURCE_CONSENT_MAP: dict[SourceType, ConsentScope] = {
    SourceType.PHOTO: ConsentScope.PHOTOGRAPHS,
    SourceType.AUDIO_RECORDING: ConsentScope.AUDIO_RECORDINGS,
    SourceType.VIDEO: ConsentScope.VIDEO_RECORDINGS,
    SourceType.MEDICAL_RECORD: ConsentScope.MEDICAL_INFORMATION,
    SourceType.BANK_RECORD: ConsentScope.FINANCIAL_INFORMATION,
    SourceType.LEASE_AGREEMENT: ConsentScope.TENANCY_RECORDS,
    SourceType.RTB_DECISION: ConsentScope.TENANCY_RECORDS,
    SourceType.EMAIL: ConsentScope.EMAIL_IMPORT,
}


@dataclass
class ConsentGateResult:
    allowed: bool
    missing_scopes: list[str]
    reason: str

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "missing_scopes": list(self.missing_scopes),
            "reason": self.reason,
        }


def consent_allows_privilege_class(
    ledger: ConsentLedger,
    *,
    matter_id: str,
    privilege_class: PrivilegeClass,
    source_type: Optional[SourceType] = None,
    client_id: str = "unknown",
) -> ConsentGateResult:
    required: list[ConsentScope] = list(
        PRIVILEGE_CONSENT_MAP.get(privilege_class, [ConsentScope.AI_ANALYSIS])
    )
    if source_type and source_type in SOURCE_CONSENT_MAP:
        sc = SOURCE_CONSENT_MAP[source_type]
        if sc.value not in {r.value for r in required}:
            required.append(sc)

    missing = [s.value for s in required if ledger.requires_scope(matter_id, s)]
    if missing:
        ledger.audit.append(
            matter_id=matter_id,
            client_id=client_id,
            action="DENY_GATE",
            scope=",".join(missing),
            detail=f"Blocked privilege_class={privilege_class.value}",
        )
        return ConsentGateResult(
            allowed=False,
            missing_scopes=missing,
            reason="Missing client consent for required scopes.",
        )
    ledger.audit.append(
        matter_id=matter_id,
        client_id=client_id,
        action="PRIVILEGE_BRIDGE",
        scope=privilege_class.value,
        detail="Consent gate passed (not a waiver)",
    )
    return ConsentGateResult(
        allowed=True,
        missing_scopes=[],
        reason="Consent scopes satisfied for processing boundary (not waiver).",
    )
