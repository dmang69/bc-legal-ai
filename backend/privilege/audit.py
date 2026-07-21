"""Append-only privilege audit log (in-memory Phase 1; persist in Postgres Phase 2)."""

from __future__ import annotations

from architecture.privilege_schemas import PrivilegeAuditEvent


class PrivilegeAuditLog:
    def __init__(self) -> None:
        self._events: list[PrivilegeAuditEvent] = []

    def append(self, event: PrivilegeAuditEvent) -> PrivilegeAuditEvent:
        self._events.append(event)
        return event

    def for_document(self, document_id: str) -> list[PrivilegeAuditEvent]:
        return [e for e in self._events if e.document_id == document_id]

    def all(self) -> list[PrivilegeAuditEvent]:
        return list(self._events)
