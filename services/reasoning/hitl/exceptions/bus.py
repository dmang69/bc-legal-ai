"""
Malpractice-aware exception bus — artifact IDs only, no raw privileged content.

CRITICAL cannot be auto-dismissed by AI; resolution requires human reason.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from services.reasoning.hitl.exceptions.escalation import (
    EscalationTarget,
    EscalationTicket,
    escalate_critical,
)
from services.reasoning.hitl.exceptions.kinds import (
    DEFAULT_SEVERITY,
    ExceptionKind,
    Severity,
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ExceptionEvent:
    event_id: str
    matter_id: str
    kind: ExceptionKind
    severity: Severity
    message: str
    summary: str = ""
    task_id: Optional[str] = None
    affected_artifacts: list[str] = field(default_factory=list)
    raw_client_content_logged: bool = False  # always False by policy
    detected_by: str = "system"
    model_id: Optional[str] = None
    prompt_template_version: Optional[str] = None
    auto_escalate: bool = False
    details: dict[str, Any] = field(default_factory=dict)
    ts: str = field(default_factory=_utcnow)
    status: str = "OPEN"  # OPEN | ASSIGNED | RESOLVED | WONT_FIX_HUMAN
    acknowledged: bool = False
    assigned_reviewer: Optional[str] = None
    resolution: Optional[str] = None
    resolution_by: Optional[str] = None
    escalation_ticket_id: Optional[str] = None
    freeze_export: bool = False
    block_workflow: bool = False
    proposed_content_quarantined: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "exception_id": self.event_id,
            "event_id": self.event_id,
            "matter_id": self.matter_id,
            "task_id": self.task_id,
            "category": self.kind.value,
            "kind": self.kind.value,
            "severity": self.severity.value,
            "summary": self.summary or self.message,
            "message": self.message,
            "affected_artifacts": list(self.affected_artifacts),
            "raw_client_content_logged": False,
            "detected_by": self.detected_by,
            "model_id": self.model_id,
            "prompt_template_version": self.prompt_template_version,
            "auto_escalate": self.auto_escalate,
            "details": dict(self.details),
            "created_at": self.ts,
            "ts": self.ts,
            "status": self.status,
            "acknowledged": self.acknowledged,
            "assigned_reviewer": self.assigned_reviewer,
            "resolution": self.resolution,
            "resolution_by": self.resolution_by,
            "escalation_ticket_id": self.escalation_ticket_id,
            "freeze_export": self.freeze_export,
            "block_workflow": self.block_workflow,
            "proposed_content_quarantined": self.proposed_content_quarantined,
        }


@dataclass
class ExceptionBus:
    events: list[ExceptionEvent] = field(default_factory=list)
    tickets: list[EscalationTicket] = field(default_factory=list)
    default_supervisor: Optional[EscalationTarget] = None
    eval_counters: dict[str, int] = field(default_factory=dict)
    frozen_matters: set[str] = field(default_factory=set)

    def emit(
        self,
        *,
        matter_id: str,
        kind: ExceptionKind | str,
        message: str,
        severity: Optional[Severity] = None,
        details: Optional[dict[str, Any]] = None,
        supervisor: Optional[EscalationTarget] = None,
        task_id: Optional[str] = None,
        affected_artifacts: Optional[list[str]] = None,
        detected_by: str = "system",
        model_id: Optional[str] = None,
        prompt_template_version: Optional[str] = None,
    ) -> ExceptionEvent:
        if isinstance(kind, str):
            kind = ExceptionKind(kind)
        # normalize aliases
        kind = ExceptionKind(kind.value)
        sev = severity or DEFAULT_SEVERITY.get(kind, Severity.INFO)
        auto = sev in (Severity.CRITICAL, Severity.HIGH)
        freeze = sev == Severity.CRITICAL
        block = sev in (Severity.CRITICAL, Severity.HIGH, Severity.WARNING)
        quarantine = kind in (
            ExceptionKind.HALLUCINATED_AUTHORITY_ATTEMPT,
            ExceptionKind.CITATION_NOT_FOUND,
            ExceptionKind.QUOTATION_MISMATCH,
        )
        # Strip any accidental raw content keys from details
        safe_details = {
            k: v
            for k, v in (details or {}).items()
            if k
            not in (
                "raw_text",
                "privileged_body",
                "medical_record",
                "full_document",
                "prompt",
                "token",
                "secret",
            )
        }
        ev = ExceptionEvent(
            event_id=f"exc_{uuid4().hex[:12]}",
            matter_id=matter_id,
            kind=kind,
            severity=sev,
            message=message,
            summary=message,
            task_id=task_id,
            affected_artifacts=list(affected_artifacts or []),
            raw_client_content_logged=False,
            detected_by=detected_by,
            model_id=model_id,
            prompt_template_version=prompt_template_version,
            auto_escalate=auto,
            details=safe_details,
            freeze_export=freeze,
            block_workflow=block,
            proposed_content_quarantined=quarantine,
        )
        if freeze:
            self.frozen_matters.add(matter_id)
        if auto:
            target = supervisor or self.default_supervisor or EscalationTarget(
                lawyer_id="SUPERVISING_LAWYER_UNASSIGNED",
                name="Unassigned — assign supervising counsel",
            )
            ticket = escalate_critical(
                event_id=ev.event_id,
                matter_id=matter_id,
                severity=sev if sev == Severity.CRITICAL else Severity.CRITICAL,
                supervising_lawyer=target,
                tickets=self.tickets,
            )
            if ticket:
                ev.escalation_ticket_id = ticket.ticket_id
                if sev == Severity.CRITICAL:
                    ticket.notes = (
                        "CRITICAL: freeze export, preserve evidence, notify supervisor; "
                        "security/privacy officer when applicable. AI cannot dismiss."
                    )
        self.events.append(ev)
        self.eval_counters[kind.value] = self.eval_counters.get(kind.value, 0) + 1
        return ev

    def log_hallucination(self, matter_id: str, message: str, **details: Any) -> ExceptionEvent:
        return self.emit(
            matter_id=matter_id,
            kind=ExceptionKind.HALLUCINATED_AUTHORITY_ATTEMPT,
            message=message,
            details=details,
            detected_by="citation_verifier",
            affected_artifacts=details.get("affected_artifacts")
            if isinstance(details.get("affected_artifacts"), list)
            else [],
        )

    def log_contradiction(self, matter_id: str, message: str, **details: Any) -> ExceptionEvent:
        return self.emit(
            matter_id=matter_id,
            kind=ExceptionKind.CONTRADICTORY_EVIDENCE,
            message=message,
            details=details,
        )

    def log_extraction_failure(self, matter_id: str, message: str, **details: Any) -> ExceptionEvent:
        return self.emit(
            matter_id=matter_id,
            kind=ExceptionKind.LOW_OCR_CONFIDENCE,
            message=message,
            details=details,
        )

    def log_legal_test(
        self,
        matter_id: str,
        *,
        status: str,
        test_id: str,
        message: str = "",
    ) -> ExceptionEvent:
        kind = (
            ExceptionKind.LEGAL_TEST_CONFLICTED
            if status.upper() == "CONFLICTED"
            else ExceptionKind.LEGAL_TEST_UNSUPPORTED
        )
        return self.emit(
            matter_id=matter_id,
            kind=kind,
            message=message or f"Legal test {test_id} → {status}",
            details={"test_id": test_id, "status": status},
            affected_artifacts=[test_id],
        )

    def open_escalations(self, matter_id: Optional[str] = None) -> list[ExceptionEvent]:
        return [
            e
            for e in self.events
            if e.auto_escalate
            and e.status == "OPEN"
            and (matter_id is None or e.matter_id == matter_id)
        ]

    def acknowledge(self, event_id: str) -> Optional[ExceptionEvent]:
        """Awareness only — does not resolve CRITICAL."""
        for e in self.events:
            if e.event_id == event_id:
                e.acknowledged = True
                if e.severity != Severity.CRITICAL:
                    e.status = "ASSIGNED"
                return e
        return None

    def resolve(
        self,
        event_id: str,
        *,
        human_id: str,
        reason: str,
    ) -> Optional[ExceptionEvent]:
        if not (reason or "").strip():
            raise ValueError("Resolution requires a human reason.")
        if not human_id or human_id.lower() in ("ai", "system", "model"):
            raise ValueError("Critical/high exceptions cannot be dismissed by the AI.")
        for e in self.events:
            if e.event_id == event_id:
                e.resolution = reason
                e.resolution_by = human_id
                e.status = "RESOLVED"
                e.acknowledged = True
                if e.severity == Severity.CRITICAL:
                    # unfreeze only if no other critical open
                    others = [
                        x
                        for x in self.events
                        if x.matter_id == e.matter_id
                        and x.severity == Severity.CRITICAL
                        and x.status == "OPEN"
                        and x.event_id != event_id
                    ]
                    if not others:
                        self.frozen_matters.discard(e.matter_id)
                return e
        return None

    def export_frozen(self, matter_id: str) -> bool:
        return matter_id in self.frozen_matters
