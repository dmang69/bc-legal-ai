"""HITL B — Error & exception logging."""

from services.reasoning.hitl.exceptions.bus import ExceptionBus, ExceptionEvent
from services.reasoning.hitl.exceptions.kinds import ExceptionKind, Severity
from services.reasoning.hitl.exceptions.escalation import EscalationTarget, escalate_critical

__all__ = [
    "ExceptionBus",
    "ExceptionEvent",
    "ExceptionKind",
    "Severity",
    "EscalationTarget",
    "escalate_critical",
]
