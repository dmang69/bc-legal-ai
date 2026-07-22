"""
Update monitors — BC Laws + CanLII currency (scaffold).

Does not scrape without licence/robots compliance. Fail-closed → MANUAL_REQUIRED.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ChangeLogEntry:
    source_id: str
    ts: str
    change_type: str  # currency_line | new_decision | template | manual
    summary: str
    prior_value: Optional[str] = None
    new_value: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "ts": self.ts,
            "change_type": self.change_type,
            "summary": self.summary,
            "prior_value": self.prior_value,
            "new_value": self.new_value,
        }


@dataclass
class UpdateCheckResult:
    source_id: str
    checked_at: str
    status: str  # UP_TO_DATE | STALE_UNKNOWN | MANUAL_REQUIRED
    message: str
    recorded_current_to: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "checked_at": self.checked_at,
            "status": self.status,
            "message": self.message,
            "recorded_current_to": self.recorded_current_to,
        }


@dataclass
class UpdateMonitor:
    change_log: list[ChangeLogEntry] = field(default_factory=list)

    def check_bc_laws(
        self, source_id: str, recorded_current_to: Optional[str] = None
    ) -> UpdateCheckResult:
        return UpdateCheckResult(
            source_id=source_id,
            checked_at=_utcnow(),
            status="MANUAL_REQUIRED",
            message=(
                "Live BC Laws fetch not wired. Open the official consolidation and "
                "compare the 'current to' line before any filing."
            ),
            recorded_current_to=recorded_current_to,
        )

    def check_canlii(self, source_id: str) -> UpdateCheckResult:
        return UpdateCheckResult(
            source_id=source_id,
            checked_at=_utcnow(),
            status="MANUAL_REQUIRED",
            message=(
                "CanLII monitor not wired. Confirm decision still good law / treatment "
                "manually before court-ready use. Respect CanLII terms of use."
            ),
        )

    def record_manual_change(
        self,
        source_id: str,
        *,
        summary: str,
        prior_value: Optional[str] = None,
        new_value: Optional[str] = None,
        change_type: str = "manual",
    ) -> ChangeLogEntry:
        entry = ChangeLogEntry(
            source_id=source_id,
            ts=_utcnow(),
            change_type=change_type,
            summary=summary,
            prior_value=prior_value,
            new_value=new_value,
        )
        self.change_log.append(entry)
        return entry
