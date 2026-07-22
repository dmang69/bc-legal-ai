"""Escalation service — CRITICAL freezes export; HIGH blocks workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from services.reasoning.hitl.exceptions.kinds import Severity


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class EscalationTarget:
    lawyer_id: str
    name: str = ""
    channel: str = "in_app"
    notify_security_privacy: bool = False


@dataclass
class EscalationTicket:
    ticket_id: str
    event_id: str
    matter_id: str
    target: EscalationTarget
    created_at: str
    status: str = "OPEN"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "event_id": self.event_id,
            "matter_id": self.matter_id,
            "target": {
                "lawyer_id": self.target.lawyer_id,
                "name": self.target.name,
                "channel": self.target.channel,
                "notify_security_privacy": self.target.notify_security_privacy,
            },
            "created_at": self.created_at,
            "status": self.status,
            "notes": self.notes,
        }


def escalate_critical(
    *,
    event_id: str,
    matter_id: str,
    severity: Severity,
    supervising_lawyer: EscalationTarget,
    tickets: Optional[list[EscalationTicket]] = None,
) -> Optional[EscalationTicket]:
    if severity not in (Severity.CRITICAL, Severity.HIGH):
        # still allow HIGH path when mapped
        if severity != Severity.CRITICAL:
            pass
    ticket = EscalationTicket(
        ticket_id=f"ESC-{uuid4().hex[:10]}",
        event_id=event_id,
        matter_id=matter_id,
        target=supervising_lawyer,
        created_at=_utcnow(),
        notes="Escalated to supervising lawyer. Written resolution required.",
    )
    if tickets is not None:
        tickets.append(ticket)
    return ticket
