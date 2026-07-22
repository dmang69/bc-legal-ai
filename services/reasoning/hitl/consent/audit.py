"""Immutable consent audit log (append-only in-memory; prod → Postgres)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ConsentAuditEntry:
    """Frozen = treat as immutable once created."""

    entry_id: str
    ts: str
    matter_id: str
    client_id: str
    action: str  # GRANT | WITHDRAW | DENY_GATE | PRIVILEGE_BRIDGE
    scope: str
    consent_id: Optional[str]
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "ts": self.ts,
            "matter_id": self.matter_id,
            "client_id": self.client_id,
            "action": self.action,
            "scope": self.scope,
            "consent_id": self.consent_id,
            "detail": self.detail,
        }


@dataclass
class ConsentAuditLog:
    """Append-only audit trail for consent operations."""

    _entries: list[ConsentAuditEntry] = field(default_factory=list)

    def append(
        self,
        *,
        matter_id: str,
        client_id: str,
        action: str,
        scope: str,
        consent_id: Optional[str] = None,
        detail: str = "",
    ) -> ConsentAuditEntry:
        entry = ConsentAuditEntry(
            entry_id=f"CAUD-{uuid4().hex[:12]}",
            ts=_utcnow(),
            matter_id=matter_id,
            client_id=client_id,
            action=action,
            scope=scope,
            consent_id=consent_id,
            detail=detail,
        )
        self._entries.append(entry)
        return entry

    @property
    def entries(self) -> tuple[ConsentAuditEntry, ...]:
        return tuple(self._entries)

    def for_matter(self, matter_id: str) -> list[ConsentAuditEntry]:
        return [e for e in self._entries if e.matter_id == matter_id]
