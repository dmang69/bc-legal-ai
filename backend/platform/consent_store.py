"""Persisted consent ledger (M1) — processing only; never privilege."""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from backend.audit import get_audit_ledger
from backend.db import get_connection, init_db
from backend.identity import AuthError, UserInfo, get_identity_service


def _cid() -> str:
    return f"consent_{uuid.uuid4().hex[:14]}"


class ConsentStore:
    def grant(
        self,
        *,
        user: UserInfo,
        matter_id: str,
        subject_id: str,
        category: str,
        purpose: str,
        notice_version: str = "privacy-notice-3.1",
        model_scope: str = "PRIVATE_INFERENCE_ONLY",
    ) -> dict[str, Any]:
        if not purpose.strip():
            raise ValueError("purpose required")
        if not get_identity_service().can_access_matter(user, matter_id, min_level="write"):
            raise AuthError("Matter access denied")
        consent_id = _cid()
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO consents
                (consent_id, matter_id, subject_id, category, purpose, model_scope,
                 status, notice_version, granted_at, captured_by)
                VALUES (?, ?, ?, ?, ?, ?, 'GRANTED', ?, datetime('now'), ?)
                """,
                (
                    consent_id,
                    matter_id,
                    subject_id,
                    category,
                    purpose.strip(),
                    model_scope,
                    notice_version,
                    user.user_id,
                ),
            )
        get_audit_ledger().append(
            actor_id=user.user_id,
            action="consent.grant",
            org_id=user.org_id,
            matter_id=matter_id,
            resource_type="consent",
            resource_id=consent_id,
            detail={"category": category, "purpose": purpose},
        )
        return self.get(consent_id)

    def withdraw(self, *, user: UserInfo, consent_id: str) -> dict[str, Any]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM consents WHERE consent_id = ?", (consent_id,)
            ).fetchone()
            if not row:
                raise AuthError("Consent not found")
            if not get_identity_service().can_access_matter(
                user, row["matter_id"], min_level="write"
            ):
                raise AuthError("Matter access denied")
            conn.execute(
                """
                UPDATE consents SET status = 'WITHDRAWN', withdrawn_at = datetime('now'),
                updated_at = datetime('now') WHERE consent_id = ?
                """,
                (consent_id,),
            )
        get_audit_ledger().append(
            actor_id=user.user_id,
            action="consent.withdraw",
            org_id=user.org_id,
            matter_id=row["matter_id"],
            resource_type="consent",
            resource_id=consent_id,
            detail={"note": "Withdrawal blocks optional AI; not unconditional delete"},
        )
        return self.get(consent_id)

    def get(self, consent_id: str) -> dict[str, Any]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM consents WHERE consent_id = ?", (consent_id,)
            ).fetchone()
        if not row:
            raise AuthError("Consent not found")
        return {
            "consent_id": row["consent_id"],
            "matter_id": row["matter_id"],
            "subject_id": row["subject_id"],
            "category": row["category"],
            "purpose": row["purpose"],
            "status": row["status"],
            "model_scope": row["model_scope"],
            "notice_version": row["notice_version"],
            "granted_at": row["granted_at"],
            "withdrawn_at": row["withdrawn_at"],
        }

    def list_for_matter(self, user: UserInfo, matter_id: str) -> list[dict[str, Any]]:
        if not get_identity_service().can_access_matter(user, matter_id):
            raise AuthError("Matter access denied")
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT consent_id, category, purpose, status FROM consents WHERE matter_id = ?",
                (matter_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def evaluate_optional_ai(self, matter_id: str) -> dict[str, Any]:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT consent_id FROM consents
                WHERE matter_id = ? AND status = 'GRANTED'
                  AND category IN ('AI_ANALYSIS', 'EXTERNAL_MODEL', 'GENERAL')
                LIMIT 1
                """,
                (matter_id,),
            ).fetchone()
        return {
            "matter_id": matter_id,
            "optional_ai_allowed": bool(row),
            "basis": "consent" if row else "none",
        }


_store: Optional[ConsentStore] = None


def get_consent_store() -> ConsentStore:
    global _store
    init_db()
    if _store is None:
        _store = ConsentStore()
    return _store
