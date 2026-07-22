"""
Version locking for completed analysis — later updates do not rewrite prior work.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AnalysisSnapshot:
    knowledge_snapshot_id: str
    matter_id: str
    statutory_version_ids: list[str]
    rules_version_ids: list[str]
    template_version_ids: list[str]
    authority_verification_time: str
    analysis_ref: str
    created_at: str = field(default_factory=_utcnow)
    change_notices: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "knowledge_snapshot_id": self.knowledge_snapshot_id,
            "matter_id": self.matter_id,
            "statutory_version_ids": list(self.statutory_version_ids),
            "rules_version_ids": list(self.rules_version_ids),
            "template_version_ids": list(self.template_version_ids),
            "authority_verification_time": self.authority_verification_time,
            "analysis_ref": self.analysis_ref,
            "created_at": self.created_at,
            "change_notices": list(self.change_notices),
        }


@dataclass
class SnapshotStore:
    snapshots: dict[str, AnalysisSnapshot] = field(default_factory=dict)

    def lock(
        self,
        *,
        matter_id: str,
        analysis_ref: str,
        statutory_version_ids: list[str],
        rules_version_ids: Optional[list[str]] = None,
        template_version_ids: Optional[list[str]] = None,
    ) -> AnalysisSnapshot:
        snap = AnalysisSnapshot(
            knowledge_snapshot_id=f"ksnap_{uuid4().hex[:12]}",
            matter_id=matter_id,
            statutory_version_ids=list(statutory_version_ids),
            rules_version_ids=list(rules_version_ids or []),
            template_version_ids=list(template_version_ids or []),
            authority_verification_time=_utcnow(),
            analysis_ref=analysis_ref,
        )
        self.snapshots[snap.knowledge_snapshot_id] = snap
        return snap

    def attach_change_notice(self, snapshot_id: str, notice: str) -> Optional[AnalysisSnapshot]:
        """Preserve original analysis; attach change notice only."""
        snap = self.snapshots.get(snapshot_id)
        if not snap:
            return None
        snap.change_notices.append(notice)
        return snap
