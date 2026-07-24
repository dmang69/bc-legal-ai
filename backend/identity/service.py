"""Organization, user, and session management with matter membership checks."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from backend.db import get_connection, init_db
from backend.identity.passwords import hash_password, hash_token, new_salt, new_token, verify_password


class AuthError(Exception):
    pass


@dataclass
class UserInfo:
    user_id: str
    org_id: str
    email: str
    display_name: str
    role: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "org_id": self.org_id,
            "email": self.email,
            "display_name": self.display_name,
            "role": self.role,
            "status": self.status,
        }


@dataclass
class SessionInfo:
    session_id: str
    user: UserInfo
    token: str
    expires_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "token": self.token,
            "expires_at": self.expires_at,
            "user": self.user.to_dict(),
        }


def _uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def _row_user(row) -> UserInfo:
    return UserInfo(
        user_id=row["user_id"],
        org_id=row["org_id"],
        email=row["email"],
        display_name=row["display_name"] or "",
        role=row["role"],
        status=row["status"],
    )


class IdentityService:
    def create_organization(self, name: str) -> str:
        org_id = _uid("org")
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO organizations (org_id, name) VALUES (?, ?)",
                (org_id, name),
            )
        return org_id

    def register_user(
        self,
        *,
        org_id: str,
        email: str,
        password: str,
        display_name: str = "",
        role: str = "member",
    ) -> UserInfo:
        if len(password) < 10:
            raise AuthError("Password must be at least 10 characters")
        user_id = _uid("user")
        salt = new_salt()
        ph = hash_password(password, salt)
        email_n = email.strip().lower()
        with get_connection() as conn:
            org = conn.execute(
                "SELECT org_id FROM organizations WHERE org_id = ?", (org_id,)
            ).fetchone()
            if not org:
                raise AuthError("Organization not found")
            try:
                conn.execute(
                    """
                    INSERT INTO users
                    (user_id, org_id, email, display_name, password_hash, password_salt, role)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, org_id, email_n, display_name, ph, salt, role),
                )
            except Exception as e:
                raise AuthError(f"Could not register user: {e}") from e
        return UserInfo(
            user_id=user_id,
            org_id=org_id,
            email=email_n,
            display_name=display_name,
            role=role,
            status="ACTIVE",
        )

    def login(
        self,
        *,
        email: str,
        password: str,
        user_agent: str = "",
        ip_hint: str = "",
        hours: int = 12,
    ) -> SessionInfo:
        email_n = email.strip().lower()
        now = datetime.now(timezone.utc)
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email_n,)
            ).fetchone()
            if not row or row["status"] != "ACTIVE":
                raise AuthError("Invalid credentials")
            if not verify_password(password, row["password_salt"], row["password_hash"]):
                raise AuthError("Invalid credentials")
            user = _row_user(row)
            token = new_token()
            session_id = _uid("sess")
            expires = now + timedelta(hours=hours)
            expires_s = expires.isoformat()
            conn.execute(
                """
                INSERT INTO sessions
                (session_id, user_id, org_id, token_hash, expires_at, user_agent, ip_hint)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    user.user_id,
                    user.org_id,
                    hash_token(token),
                    expires_s,
                    user_agent[:200],
                    ip_hint[:64],
                ),
            )
            conn.execute(
                "UPDATE users SET last_login_at = ? WHERE user_id = ?",
                (now.isoformat(), user.user_id),
            )
        return SessionInfo(
            session_id=session_id,
            user=user,
            token=token,
            expires_at=expires_s,
        )

    def resolve_token(self, token: str) -> UserInfo:
        th = hash_token(token)
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT u.*, s.expires_at, s.revoked_at
                FROM sessions s
                JOIN users u ON u.user_id = s.user_id
                WHERE s.token_hash = ?
                """,
                (th,),
            ).fetchone()
            if not row:
                raise AuthError("Invalid session")
            if row["revoked_at"]:
                raise AuthError("Session revoked")
            # naive ISO compare works for our stored format
            if row["expires_at"] < datetime.now(timezone.utc).isoformat():
                raise AuthError("Session expired")
            if row["status"] != "ACTIVE":
                raise AuthError("Account not active")
            return _row_user(row)

    def revoke_session(self, token: str) -> None:
        th = hash_token(token)
        with get_connection() as conn:
            conn.execute(
                "UPDATE sessions SET revoked_at = ? WHERE token_hash = ?",
                (datetime.now(timezone.utc).isoformat(), th),
            )

    def grant_matter_access(
        self,
        *,
        matter_id: str,
        user_id: str,
        access_level: str = "write",
        granted_by: str = "system",
    ) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO matter_members
                (matter_id, user_id, access_level, granted_by, revoked_at)
                VALUES (?, ?, ?, ?, NULL)
                ON CONFLICT(matter_id, user_id) DO UPDATE SET
                  access_level = excluded.access_level,
                  granted_by = excluded.granted_by,
                  revoked_at = NULL
                """,
                (matter_id, user_id, access_level, granted_by),
            )

    def can_access_matter(
        self, user: UserInfo, matter_id: str, *, min_level: str = "read"
    ) -> bool:
        """Deny-first authorization: ethical wall check takes priority over all roles.

        Authorization order:
        1. Validate matter exists and belongs to user's org.
        2. Check explicit denial, revocation, or ethical-wall membership.
        3. Deny regardless of role if an explicit denial exists.
        4. Apply role-based access only when no explicit denial exists.
        """
        order = {"read": 1, "write": 2, "admin": 3, "ethical_wall": 0}
        with get_connection() as conn:
            m = conn.execute(
                "SELECT org_id FROM matters WHERE matter_id = ?", (matter_id,)
            ).fetchone()
            if not m:
                return False
            if m["org_id"] and m["org_id"] != user.org_id:
                return False

            # Check for explicit denial (ethical_wall or revoked) FIRST — overrides all roles
            mem = conn.execute(
                """
                SELECT access_level, revoked_at FROM matter_members
                WHERE matter_id = ? AND user_id = ?
                """,
                (matter_id, user.user_id),
            ).fetchone()

            # Explicit denial: ethical wall or revoked membership
            if mem:
                if mem["access_level"] == "ethical_wall":
                    return False  # Ethical wall blocks ALL roles, including owner/admin
                if mem["revoked_at"] is not None:
                    return False  # Revoked membership blocks all access

            # No explicit denial found — apply role-based access
            if user.role in ("owner", "admin"):
                return True

            # Non-owner/admin must have an active granted membership
            if not mem:
                return False  # No membership record at all
            return order.get(mem["access_level"], 0) >= order.get(min_level, 1)


_svc: Optional[IdentityService] = None


def get_identity_service() -> IdentityService:
    global _svc
    init_db()
    if _svc is None:
        _svc = IdentityService()
    return _svc
