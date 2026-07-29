"""Authentication logic — Argon2 password hashing and server-side sessions.

Ported from Phase 1's auth/core.py to SQLAlchemy 2.0 ORM.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.config import get_settings
from app.models import Session, User

SESSION_COOKIE_NAME = "eap_session"
SESSION_TTL = timedelta(days=7)
SESSION_ROLLING_REFRESH = timedelta(hours=6)

_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=64 * 1024,
    parallelism=2,
    hash_len=32,
    salt_len=16,
)

_COMMON_PASSWORDS = frozenset({
    "password", "password1", "password123", "12345678", "123456789",
    "qwertyui", "letmein12", "iloveyou1", "admin123", "welcome1",
    "changeme", "changeme1", "enterpriseai",
})
MIN_PASSWORD_LENGTH = 12


# --- Password ---------------------------------------------------------------

def validate_password_strength(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(400, f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if password.lower() in _COMMON_PASSWORDS:
        raise HTTPException(400, "Password is on the common-password deny-list.")
    if password.isdigit() or password.isalpha():
        raise HTTPException(400, "Password must include a mix of character classes.")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(stored_hash: str, password: str) -> bool:
    try:
        _hasher.verify(stored_hash, password)
        return True
    except (VerifyMismatchError, InvalidHashError):
        return False


def needs_rehash(stored_hash: str) -> bool:
    return _hasher.check_needs_rehash(stored_hash)


# --- User CRUD --------------------------------------------------------------

def create_user(
    db: DbSession,
    email: str,
    password: str,
    display_name: str,
    role: str = "user",
) -> User:
    email = email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(400, "Invalid email.")
    if not display_name.strip():
        raise HTTPException(400, "Display name required.")
    validate_password_strength(password)

    # Uniqueness check up-front for a clean 409
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(409, "Email already registered.")

    user = User(
        email=email,
        password_hash=hash_password(password),
        display_name=display_name.strip(),
        role=role,
    )
    db.add(user)
    db.flush()  # populate id without committing
    return user


def get_user_by_email(db: DbSession, email: str) -> Optional[User]:
    return db.scalar(select(User).where(User.email == email.strip().lower()))


def get_user_by_id(db: DbSession, user_id: int) -> Optional[User]:
    return db.get(User, user_id)


def count_users(db: DbSession) -> int:
    return db.scalar(select(User).with_only_columns(User.id).order_by(None).limit(1)) is not None \
        and db.query(User).count() or 0


# --- Sessions ---------------------------------------------------------------

def _new_session_token() -> str:
    return secrets.token_urlsafe(32)


def create_session(
    db: DbSession,
    user_id: int,
    user_agent: Optional[str],
    ip_hash: Optional[str],
) -> str:
    token = _new_session_token()
    now = datetime.now(timezone.utc)
    session = Session(
        id=token,
        user_id=user_id,
        expires_at=now + SESSION_TTL,
        last_used_at=now,
        user_agent=(user_agent or "")[:512] or None,
        ip_hash=ip_hash,
    )
    db.add(session)
    db.flush()
    return token


def revoke_session(db: DbSession, token: str) -> None:
    session = db.get(Session, token)
    if session and session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)
        db.flush()


def revoke_all_user_sessions(db: DbSession, user_id: int) -> None:
    now = datetime.now(timezone.utc)
    for session in db.scalars(
        select(Session).where(Session.user_id == user_id, Session.revoked_at.is_(None))
    ):
        session.revoked_at = now
    db.flush()


def lookup_session(db: DbSession, token: str) -> Optional[Session]:
    session = db.get(Session, token)
    if not session or session.revoked_at is not None:
        return None
    now = datetime.now(timezone.utc)
    if now >= session.expires_at:
        return None

    # Rolling refresh
    if now - session.last_used_at > SESSION_ROLLING_REFRESH:
        session.expires_at = now + SESSION_TTL
    session.last_used_at = now
    db.flush()
    return session


# --- Cookie helpers ---------------------------------------------------------

def set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.EAP_COOKIE_SECURE,
        samesite="lax",
        max_age=int(SESSION_TTL.total_seconds()),
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=settings.EAP_COOKIE_SECURE,
        samesite="lax",
    )


def hash_ip(ip: Optional[str]) -> Optional[str]:
    if not ip:
        return None
    return hashlib.sha256(ip.encode()).hexdigest()[:16]
