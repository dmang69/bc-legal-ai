"""
Case status dashboard — matter snapshot for hearing / petition workflow.

Not legal advice. Deadlines and strength labels are planning tools;
confirm every date and assessment before reliance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class CaseType(str, Enum):
    RTB_DISPUTE = "RTB_DISPUTE"
    JUDICIAL_REVIEW = "JUDICIAL_REVIEW"
    OTHER = "OTHER"


class WorkflowStatus(str, Enum):
    INTAKE = "INTAKE"
    EVIDENCE_GATHERING = "EVIDENCE_GATHERING"
    ANALYSIS = "ANALYSIS"
    DRAFTING = "DRAFTING"
    REVIEW_PENDING = "REVIEW_PENDING"
    READY_FOR_COUNSEL = "READY_FOR_COUNSEL"
    FILED = "FILED"
    CLOSED = "CLOSED"


class GroundStrength(str, Enum):
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNKNOWN = "UNKNOWN"


class NextActionState(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    BLOCKED = "BLOCKED"


@dataclass
class MissingItem:
    label: str
    status_note: str = ""  # e.g. requested, awaiting from RTB
    blocking: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "status_note": self.status_note,
            "blocking": self.blocking,
        }

    def format_line(self) -> str:
        extra = f" ({self.status_note})" if self.status_note else ""
        return f"Missing: {self.label}{extra}"


@dataclass
class GroundStatus:
    label: str
    strength: GroundStrength
    notes: str = ""
    related_ground_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "strength": self.strength.value,
            "notes": self.notes,
            "related_ground_ids": list(self.related_ground_ids),
        }

    def format_line(self) -> str:
        return f" ● {self.label} — {self.strength.value.replace('_', ' ')}"


@dataclass
class NextAction:
    description: str
    state: NextActionState = NextActionState.PENDING

    def to_dict(self) -> dict[str, Any]:
        return {"description": self.description, "state": self.state.value}

    def format_line(self) -> str:
        return f"NEXT ACTION: {self.description} [{self.state.value}]"


@dataclass
class CaseDashboard:
    """
    Status board for a matter (JR petition, RTB dispute, etc.).
    """

    dashboard_id: str = field(default_factory=lambda: f"DASH-{uuid4().hex[:8]}")
    case_title: str = ""
    file_number: str = ""
    case_type: CaseType = CaseType.JUDICIAL_REVIEW
    matter_id: Optional[str] = None
    workflow_status: WorkflowStatus = WorkflowStatus.DRAFTING
    status_label: str = ""  # free text e.g. Petition drafting in progress
    deadline: Optional[str] = None  # YYYY-MM-DD
    deadline_label: str = ""  # e.g. petition filing / JRPA limitation
    next_action: Optional[NextAction] = None
    evidence_complete_pct: int = 0  # 0–100
    missing_items: list[MissingItem] = field(default_factory=list)
    legal_grounds: list[GroundStatus] = field(default_factory=list)
    strength_assessment_note: str = (
        "[Full assessment requires lawyer review]"
    )
    as_of: Optional[str] = None  # YYYY-MM-DD for days-remaining snapshot
    notes: str = ""
    disclaimer: str = (
        "Case dashboard for workbench planning only. Not legal advice. "
        "Confirm every deadline, limitation period, and strength label with counsel "
        "and primary sources before relying."
    )

    def days_remaining(self, as_of: Optional[date] = None) -> Optional[int]:
        if not self.deadline:
            return None
        try:
            target = date.fromisoformat(self.deadline[:10])
        except ValueError:
            return None
        if as_of is None:
            if self.as_of:
                try:
                    as_of = date.fromisoformat(self.as_of[:10])
                except ValueError:
                    as_of = date.today()
            else:
                as_of = date.today()
        return (target - as_of).days

    def deadline_banner(self, as_of: Optional[date] = None) -> str:
        if not self.deadline:
            return "DEADLINE: (not set)"
        days = self.days_remaining(as_of)
        try:
            d = date.fromisoformat(self.deadline[:10])
            pretty = d.strftime("%B %d, %Y")
        except ValueError:
            pretty = self.deadline
        if days is None:
            return f"DEADLINE: {pretty}"
        if days > 0:
            return f"DEADLINE: {pretty} ({days} days remaining)"
        if days == 0:
            return f"DEADLINE: {pretty} (DUE TODAY)"
        return f"DEADLINE: {pretty} ({abs(days)} days OVERDUE)"

    def evidence_bar(self, width: int = 15) -> str:
        pct = max(0, min(100, int(self.evidence_complete_pct)))
        filled = round(width * pct / 100)
        empty = width - filled
        return "█" * filled + "░" * empty + f" {pct}% complete"

    def to_dict(self) -> dict[str, Any]:
        return {
            "dashboard_id": self.dashboard_id,
            "case_title": self.case_title,
            "file_number": self.file_number,
            "case_type": self.case_type.value,
            "matter_id": self.matter_id,
            "workflow_status": self.workflow_status.value,
            "status_label": self.status_label,
            "deadline": self.deadline,
            "deadline_label": self.deadline_label,
            "days_remaining": self.days_remaining(),
            "next_action": self.next_action.to_dict() if self.next_action else None,
            "evidence_complete_pct": self.evidence_complete_pct,
            "missing_items": [m.to_dict() for m in self.missing_items],
            "legal_grounds": [g.to_dict() for g in self.legal_grounds],
            "strength_assessment_note": self.strength_assessment_note,
            "as_of": self.as_of,
            "notes": self.notes,
            "disclaimer": self.disclaimer,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "CaseDashboard":
        na = data.get("next_action")
        return CaseDashboard(
            dashboard_id=str(data.get("dashboard_id") or f"DASH-{uuid4().hex[:8]}"),
            case_title=str(data.get("case_title") or ""),
            file_number=str(data.get("file_number") or ""),
            case_type=CaseType(data.get("case_type", CaseType.JUDICIAL_REVIEW.value)),
            matter_id=data.get("matter_id"),
            workflow_status=WorkflowStatus(
                data.get("workflow_status", WorkflowStatus.DRAFTING.value)
            ),
            status_label=str(data.get("status_label") or ""),
            deadline=data.get("deadline"),
            deadline_label=str(data.get("deadline_label") or ""),
            next_action=NextAction(
                description=str(na.get("description") or ""),
                state=NextActionState(na.get("state", NextActionState.PENDING.value)),
            )
            if na
            else None,
            evidence_complete_pct=int(data.get("evidence_complete_pct") or 0),
            missing_items=[
                MissingItem(**m) if isinstance(m, dict) else MissingItem(label=str(m))
                for m in (data.get("missing_items") or [])
            ],
            legal_grounds=[
                GroundStatus(
                    label=str(g.get("label") or ""),
                    strength=GroundStrength(
                        g.get("strength", GroundStrength.UNKNOWN.value)
                    ),
                    notes=str(g.get("notes") or ""),
                    related_ground_ids=list(g.get("related_ground_ids") or []),
                )
                for g in (data.get("legal_grounds") or [])
            ],
            strength_assessment_note=str(
                data.get("strength_assessment_note")
                or "[Full assessment requires lawyer review]"
            ),
            as_of=data.get("as_of"),
            notes=str(data.get("notes") or ""),
            disclaimer=str(
                data.get("disclaimer")
                or CaseDashboard().disclaimer
            ),
        )

    def format_dashboard(self, as_of: Optional[date] = None) -> str:
        """ASCII status board matching workbench case view."""
        status = self.status_label or self.workflow_status.value.replace("_", " ").title()
        next_line = (
            self.next_action.format_line()
            if self.next_action
            else "NEXT ACTION: (none set)"
        )
        box_inner = [
            f" STATUS: {status}",
            f" {self.deadline_banner(as_of)}",
            f" {next_line}",
        ]
        # pad box
        width = max(len(x) for x in box_inner) + 1
        width = max(width, 45)
        top = "┌" + "─" * width + "┐"
        bot = "└" + "─" * width + "┘"
        mid = [f"│{line.ljust(width)}│" for line in box_inner]

        lines = [
            f"YOUR CASE: {self.case_title or self.case_type.value}",
            f"File: {self.file_number or '(none)'}",
            "",
            top,
            *mid,
            bot,
            "",
            "EVIDENCE INVENTORY:",
            f" {self.evidence_bar()}",
        ]
        for m in self.missing_items:
            lines.append(f" {m.format_line()}")
        if not self.missing_items:
            lines.append(" (no missing items listed)")
        lines.append("")
        lines.append("LEGAL GROUNDS IDENTIFIED:")
        for g in self.legal_grounds:
            lines.append(g.format_line())
        if not self.legal_grounds:
            lines.append(" (none listed)")
        lines.append("")
        lines.append("STRENGTH ASSESSMENT:")
        lines.append(f" {self.strength_assessment_note}")
        if self.notes:
            lines.append("")
            lines.append(f"Notes: {self.notes}")
        lines.append("")
        lines.append(f"> {self.disclaimer}")
        return "\n".join(lines)
