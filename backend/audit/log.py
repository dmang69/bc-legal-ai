"""
Append-only JSONL audit log per matter.

matters/{matter_id}/audit/events.jsonl
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, Optional

from architecture.audit_event import AuditAction, AuditEvent


class AuditLog:
    def __init__(self, matter_id: str, *, root: Optional[Path] = None) -> None:
        if not matter_id or "/" in matter_id or "\\" in matter_id or ".." in matter_id:
            raise ValueError("matter_id must be path-safe")
        self.matter_id = matter_id
        self.root = (root or Path("matters")).resolve()

    @property
    def path(self) -> Path:
        return self.root / self.matter_id / "audit" / "events.jsonl"

    def append(self, event: AuditEvent) -> AuditEvent:
        event.matter_id = event.matter_id or self.matter_id
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        return event

    def iter_events(self) -> Iterator[AuditEvent]:
        if not self.path.is_file():
            return
        with self.path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield AuditEvent.from_dict(json.loads(line))

    def list_events(
        self,
        *,
        action: Optional[AuditAction] = None,
        limit: int = 1000,
    ) -> list[AuditEvent]:
        out: list[AuditEvent] = []
        for ev in self.iter_events() or []:
            if action and ev.action != action:
                continue
            out.append(ev)
        return out[-limit:]

    def latest(self, action: Optional[AuditAction] = None) -> Optional[AuditEvent]:
        events = self.list_events(action=action, limit=10_000)
        return events[-1] if events else None
