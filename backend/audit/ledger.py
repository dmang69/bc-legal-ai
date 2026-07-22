"""Append-only hash-chained audit ledger (M1)."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any, Optional

from backend.db import get_connection, init_db

GENESIS = "0" * 64


def _uid() -> str:
    return f"aud_{uuid.uuid4().hex}"


def _canonical(detail: dict[str, Any]) -> str:
    return json.dumps(detail, sort_keys=True, separators=(",", ":"), default=str)


def _hash_entry(
    prev_hash: str,
    event_id: str,
    actor_id: str,
    action: str,
    org_id: str,
    matter_id: str,
    resource_type: str,
    resource_id: str,
    detail_s: str,
) -> str:
    payload = "|".join(
        [
            prev_hash,
            event_id,
            actor_id,
            action,
            org_id,
            matter_id,
            resource_type,
            resource_id,
            detail_s,
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class AuditEvent:
    event_id: str
    seq: int
    actor_id: str
    action: str
    entry_hash: str
    prev_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "seq": self.seq,
            "actor_id": self.actor_id,
            "action": self.action,
            "entry_hash": self.entry_hash,
            "prev_hash": self.prev_hash,
        }


class AuditLedger:
    def append(
        self,
        *,
        actor_id: str,
        action: str,
        org_id: str = "",
        matter_id: str = "",
        resource_type: str = "",
        resource_id: str = "",
        detail: Optional[dict[str, Any]] = None,
    ) -> AuditEvent:
        detail = detail or {}
        detail_s = _canonical(detail)
        event_id = _uid()
        with get_connection() as conn:
            row = conn.execute(
                "SELECT entry_hash FROM audit_ledger ORDER BY seq DESC LIMIT 1"
            ).fetchone()
            prev = row["entry_hash"] if row else GENESIS
            entry_hash = _hash_entry(
                prev,
                event_id,
                actor_id,
                action,
                org_id,
                matter_id,
                resource_type,
                resource_id,
                detail_s,
            )
            conn.execute(
                """
                INSERT INTO audit_ledger
                (event_id, org_id, matter_id, actor_id, action, resource_type,
                 resource_id, detail, prev_hash, entry_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    org_id,
                    matter_id,
                    actor_id,
                    action,
                    resource_type,
                    resource_id,
                    detail_s,
                    prev,
                    entry_hash,
                ),
            )
            seq_row = conn.execute(
                "SELECT seq FROM audit_ledger WHERE event_id = ?", (event_id,)
            ).fetchone()
            seq = int(seq_row["seq"])
        return AuditEvent(
            event_id=event_id,
            seq=seq,
            actor_id=actor_id,
            action=action,
            entry_hash=entry_hash,
            prev_hash=prev,
        )

    def verify_chain(self, *, limit: int = 10_000) -> dict[str, Any]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_ledger ORDER BY seq ASC LIMIT ?", (limit,)
            ).fetchall()
        prev = GENESIS
        for r in rows:
            expected = _hash_entry(
                prev,
                r["event_id"],
                r["actor_id"],
                r["action"],
                r["org_id"] or "",
                r["matter_id"] or "",
                r["resource_type"] or "",
                r["resource_id"] or "",
                r["detail"] or "{}",
            )
            if r["prev_hash"] != prev or r["entry_hash"] != expected:
                return {
                    "ok": False,
                    "broken_at_seq": r["seq"],
                    "event_id": r["event_id"],
                }
            prev = r["entry_hash"]
        return {"ok": True, "entries_checked": len(rows)}


_ledger: Optional[AuditLedger] = None


def get_audit_ledger() -> AuditLedger:
    global _ledger
    init_db()
    if _ledger is None:
        _ledger = AuditLedger()
    return _ledger
