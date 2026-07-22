"""Basic conflict search (exact + normalized name)."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

from backend.audit import get_audit_ledger
from backend.db import get_connection, init_db
from backend.identity import UserInfo


def _normalize(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def _cid() -> str:
    return f"cfl_{uuid.uuid4().hex[:16]}"


class ConflictService:
    def add_party(
        self,
        *,
        user: UserInfo,
        display_name: str,
        party_type: str = "person",
        aliases: list[str] | None = None,
    ) -> dict[str, Any]:
        party_id = f"pty_{uuid.uuid4().hex[:12]}"
        norm = _normalize(display_name)
        aliases = aliases or []
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO parties
                (party_id, org_id, display_name, name_normalized, party_type, aliases)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    party_id,
                    user.org_id,
                    display_name.strip(),
                    norm,
                    party_type,
                    json.dumps(aliases),
                ),
            )
        return {
            "party_id": party_id,
            "display_name": display_name.strip(),
            "name_normalized": norm,
        }

    def link_party_to_matter(
        self, *, matter_id: str, party_id: str, role: str
    ) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO matter_parties (matter_id, party_id, role)
                VALUES (?, ?, ?)
                """,
                (matter_id, party_id, role),
            )

    def check_name(
        self, *, user: UserInfo, query_name: str, matter_id: str | None = None
    ) -> dict[str, Any]:
        norm = _normalize(query_name)
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT p.*, mp.matter_id, mp.role
                FROM parties p
                LEFT JOIN matter_parties mp ON mp.party_id = p.party_id
                WHERE p.org_id = ? AND (
                  p.name_normalized = ?
                  OR p.display_name LIKE ?
                  OR p.aliases LIKE ?
                )
                """,
                (user.org_id, norm, f"%{query_name.strip()}%", f"%{norm}%"),
            ).fetchall()
        hits = [
            {
                "party_id": r["party_id"],
                "display_name": r["display_name"],
                "matter_id": r["matter_id"],
                "role": r["role"],
            }
            for r in rows
        ]
        check_id = _cid()
        status = "CLEAR" if not hits else "PENDING_REVIEW"
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO conflict_checks
                (check_id, org_id, matter_id, query_name, status, hits_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    check_id,
                    user.org_id,
                    matter_id,
                    query_name.strip(),
                    status,
                    json.dumps(hits),
                ),
            )
        get_audit_ledger().append(
            actor_id=user.user_id,
            action="conflict.check",
            org_id=user.org_id,
            matter_id=matter_id or "",
            resource_type="conflict_check",
            resource_id=check_id,
            detail={"query": query_name, "hit_count": len(hits), "status": status},
        )
        return {
            "check_id": check_id,
            "status": status,
            "hits": hits,
            "review_required": status != "CLEAR",
        }


def get_conflict_service() -> ConflictService:
    init_db()
    return ConflictService()
