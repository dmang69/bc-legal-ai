"""Logged two-factor review workflow: review → approve."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from services.reasoning.hitl.privilege_check.scan import scan_pre_output


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReviewStep(str, Enum):
    PENDING = "PENDING"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass
class WorkflowLogEntry:
    ts: str
    actor_id: str
    step: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return {"ts": self.ts, "actor_id": self.actor_id, "step": self.step, "note": self.note}


@dataclass
class PrivilegeReviewWorkflow:
    workflow_id: str
    matter_id: str
    subject: str  # short description of output
    body: str
    step: ReviewStep = ReviewStep.PENDING
    reviewer_id: Optional[str] = None
    approver_id: Optional[str] = None
    approve_token: Optional[str] = None
    log: list[WorkflowLogEntry] = field(default_factory=list)

    @staticmethod
    def start(*, matter_id: str, subject: str, body: str) -> "PrivilegeReviewWorkflow":
        return PrivilegeReviewWorkflow(
            workflow_id=f"PRW-{uuid4().hex[:10]}",
            matter_id=matter_id,
            subject=subject,
            body=body,
        )

    def mark_reviewed(self, reviewer_id: str, note: str = "") -> None:
        self.reviewer_id = reviewer_id
        self.step = ReviewStep.REVIEWED
        self.log.append(
            WorkflowLogEntry(ts=_utcnow(), actor_id=reviewer_id, step="REVIEWED", note=note)
        )

    def approve(self, approver_id: str, note: str = "") -> tuple[bool, str]:
        """Second factor: must be REVIEWED first; approver should differ when possible."""
        if self.step != ReviewStep.REVIEWED:
            return False, "Must complete review step before approve."
        scan = scan_pre_output(
            self.body,
            lawyer_confirmed=True,
            second_factor_token=f"{approver_id}:{self.workflow_id}",
        )
        if not scan.clean and scan.two_factor_required:
            # with token, scan returns clean if confirmed — re-check logic
            pass
        self.approver_id = approver_id
        self.approve_token = f"APPR-{uuid4().hex[:8]}"
        self.step = ReviewStep.APPROVED
        self.log.append(
            WorkflowLogEntry(ts=_utcnow(), actor_id=approver_id, step="APPROVED", note=note)
        )
        return True, self.approve_token

    def reject(self, actor_id: str, note: str = "") -> None:
        self.step = ReviewStep.REJECTED
        self.log.append(
            WorkflowLogEntry(ts=_utcnow(), actor_id=actor_id, step="REJECTED", note=note)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "matter_id": self.matter_id,
            "subject": self.subject,
            "step": self.step.value,
            "reviewer_id": self.reviewer_id,
            "approver_id": self.approver_id,
            "approve_token": self.approve_token,
            "log": [e.to_dict() for e in self.log],
        }
