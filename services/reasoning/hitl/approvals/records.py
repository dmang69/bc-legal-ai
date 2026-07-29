"""Approval records for HITL two-step professional actions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ApprovalRecord:
    approval_id: str
    matter_id: str
    production_id: str
    stage: str  # REVIEW | APPROVE
    actor_id: str
    decision: str  # APPROVED | REJECTED
    notes: str = ""
    snapshot_hash: str = ""
    ts: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "matter_id": self.matter_id,
            "production_id": self.production_id,
            "stage": self.stage,
            "actor_id": self.actor_id,
            "decision": self.decision,
            "notes": self.notes,
            "snapshot_hash": self.snapshot_hash,
            "ts": self.ts,
        }


@dataclass
class ApprovalRegistry:
    records: list[ApprovalRecord] = field(default_factory=list)

    def add(
        self,
        *,
        matter_id: str,
        production_id: str,
        stage: str,
        actor_id: str,
        decision: str,
        notes: str = "",
        snapshot_hash: str = "",
    ) -> ApprovalRecord:
        rec = ApprovalRecord(
            approval_id=f"appr_{uuid4().hex[:10]}",
            matter_id=matter_id,
            production_id=production_id,
            stage=stage,
            actor_id=actor_id,
            decision=decision,
            notes=notes,
            snapshot_hash=snapshot_hash,
        )
        self.records.append(rec)
        return rec
