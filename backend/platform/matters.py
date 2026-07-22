"""Org-scoped matter store with membership grants (M1 isolation)."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from backend.audit import get_audit_ledger
from backend.db import get_connection, init_db
from backend.identity import AuthError, UserInfo, get_identity_service


def _mid() -> str:
    return f"mat_{uuid.uuid4().hex[:16]}"


class MatterStore:
    def create_matter(
        self,
        *,
        user: UserInfo,
        title: str,
        client_label: str = "",
        synthetic: bool = False,
    ) -> dict[str, Any]:
        if not synthetic and False:  # real-matter path reserved
            pass
        matter_id = _mid()
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO matters
                (matter_id, title, org_id, client_label, synthetic, status)
                VALUES (?, ?, ?, ?, ?, 'OPEN')
                """,
                (
                    matter_id,
                    title,
                    user.org_id,
                    client_label,
                    1 if synthetic else 0,
                ),
            )
        idsvc = get_identity_service()
        idsvc.grant_matter_access(
            matter_id=matter_id,
            user_id=user.user_id,
            access_level="admin",
            granted_by=user.user_id,
        )
        get_audit_ledger().append(
            actor_id=user.user_id,
            action="matter.create",
            org_id=user.org_id,
            matter_id=matter_id,
            resource_type="matter",
            resource_id=matter_id,
            detail={"title": title, "synthetic": synthetic},
        )
        return self.get_matter(user, matter_id)

    def get_matter(self, user: UserInfo, matter_id: str) -> dict[str, Any]:
        idsvc = get_identity_service()
        if not idsvc.can_access_matter(user, matter_id):
            raise AuthError("Matter access denied")
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM matters WHERE matter_id = ?", (matter_id,)
            ).fetchone()
        if not row:
            raise AuthError("Matter not found")
        return {
            "matter_id": row["matter_id"],
            "title": row["title"],
            "org_id": row["org_id"],
            "status": row["status"],
            "client_label": row["client_label"],
            "synthetic": bool(row["synthetic"]),
            "created_at": row["created_at"],
        }

    def list_matters(self, user: UserInfo) -> list[dict[str, Any]]:
        with get_connection() as conn:
            if user.role in ("owner", "admin"):
                rows = conn.execute(
                    "SELECT * FROM matters WHERE org_id = ? ORDER BY created_at DESC",
                    (user.org_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT m.* FROM matters m
                    JOIN matter_members mm ON mm.matter_id = m.matter_id
                    WHERE m.org_id = ? AND mm.user_id = ? AND mm.revoked_at IS NULL
                      AND mm.access_level != 'ethical_wall'
                    ORDER BY m.created_at DESC
                    """,
                    (user.org_id, user.user_id),
                ).fetchall()
        return [
            {
                "matter_id": r["matter_id"],
                "title": r["title"],
                "status": r["status"],
                "synthetic": bool(r["synthetic"]),
            }
            for r in rows
        ]


_store: Optional[MatterStore] = None


def get_matter_store() -> MatterStore:
    global _store
    init_db()
    if _store is None:
        _store = MatterStore()
    return _store
