"""
Escalation routing for non-compliance events.

Paths: RTB enforcement | Provincial Court filing | Garnishment workflow.
Not legal advice — pathway choice requires lawyer judgment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from services.post_resolution.compliance_monitor.monitor import (
    NonComplianceEvent,
    NonComplianceKind,
)
from services.post_resolution.obligation_parser.parser import ObligationKind


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class EscalationPath(str, Enum):
    RTB_ENFORCEMENT = "RTB_ENFORCEMENT"
    PROVINCIAL_COURT = "PROVINCIAL_COURT"
    GARNISHMENT = "GARNISHMENT"
    JR_REVIEW = "JR_REVIEW"
    MANUAL = "MANUAL"


@dataclass
class EscalationTicket:
    ticket_id: str
    matter_id: str
    path: EscalationPath
    source_event_id: str
    reason: str
    status: str = "OPEN"
    created_at: str = field(default_factory=_utcnow)
    next_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "matter_id": self.matter_id,
            "path": self.path.value,
            "source_event_id": self.source_event_id,
            "reason": self.reason,
            "status": self.status,
            "created_at": self.created_at,
            "next_steps": list(self.next_steps),
        }


_PATH_STEPS: dict[EscalationPath, list[str]] = {
    EscalationPath.RTB_ENFORCEMENT: [
        "Confirm order is final and enforceable under current RTB procedures.",
        "Gather non-compliance evidence (photos, correspondence, ledger).",
        "Prepare RTB enforcement application (see enforcement package).",
    ],
    EscalationPath.PROVINCIAL_COURT: [
        "Confirm monetary award and certification path for Provincial Court.",
        "Assemble filing package + affidavit of non-payment.",
        "Calendar filing and service deadlines with counsel.",
    ],
    EscalationPath.GARNISHMENT: [
        "Confirm judgment/order supports garnishment in BC.",
        "Identify debtor income/bank sources lawfully.",
        "Draft garnishment forms + supporting affidavit under lawyer review.",
    ],
    EscalationPath.JR_REVIEW: [
        "Assess JRPA limitation (often ~60 days — confirm with counsel).",
        "Extract procedural fairness / reasonableness / jurisdiction grounds.",
        "Draft Form 67 petition scaffold + consider stay.",
    ],
    EscalationPath.MANUAL: [
        "Supervising lawyer to select pathway.",
    ],
}


@dataclass
class EscalationRouter:
    tickets: list[EscalationTicket] = field(default_factory=list)

    def route_event(
        self,
        event: NonComplianceEvent,
        *,
        obligation_kind: Optional[str] = None,
        monetary: bool = False,
        unfavorable_for_client: bool = False,
    ) -> EscalationTicket:
        path = EscalationPath.MANUAL
        if unfavorable_for_client:
            path = EscalationPath.JR_REVIEW
        elif monetary or obligation_kind == ObligationKind.MONETARY.value:
            if event.kind == NonComplianceKind.MISSED_DEADLINE:
                path = EscalationPath.PROVINCIAL_COURT
            else:
                path = EscalationPath.GARNISHMENT
        elif obligation_kind in (
            ObligationKind.REPAIR.value,
            ObligationKind.CONDUCT.value,
            ObligationKind.VACATE.value,
            ObligationKind.POSSESSION.value,
        ):
            path = EscalationPath.RTB_ENFORCEMENT

        ticket = EscalationTicket(
            ticket_id=f"ESC-PR-{uuid4().hex[:10]}",
            matter_id=event.matter_id,
            path=path,
            source_event_id=event.event_id,
            reason=event.message,
            next_steps=list(_PATH_STEPS[path]),
        )
        event.escalated = True
        self.tickets.append(ticket)
        return ticket

    def route_many(
        self,
        events: list[NonComplianceEvent],
        *,
        obligation_kinds: Optional[dict[str, str]] = None,
    ) -> list[EscalationTicket]:
        kinds = obligation_kinds or {}
        return [
            self.route_event(e, obligation_kind=kinds.get(e.obligation_id))
            for e in events
        ]
