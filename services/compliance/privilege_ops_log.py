"""Logging hooks for privilege-sensitive operations (scaffold)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class PrivilegeOpLog:
    """In-memory store for dev; production → Postgres/time-series audit."""

    entries: list[dict[str, Any]] = field(default_factory=list)

    def record(
        self,
        *,
        matter_id: str,
        operation: str,
        actor_id: str,
        privilege_class: str,
        detail: Optional[dict[str, Any]] = None,
        blocked: bool = False,
    ) -> dict[str, Any]:
        entry = {
            "id": f"PRIV-LOG-{uuid4().hex[:12]}",
            "ts": _utcnow(),
            "matter_id": matter_id,
            "operation": operation,
            "actor_id": actor_id,
            "privilege_class": privilege_class,
            "blocked": blocked,
            "detail": detail or {},
        }
        self.entries.append(entry)
        return entry
