"""Password hashing (PBKDF2-HMAC-SHA256) — no external crypto dependency."""

from __future__ import annotations

import hashlib
import hmac
import secrets


def new_salt() -> str:
    return secrets.token_hex(16)


def hash_password(password: str, salt: str, *, iterations: int = 200_000) -> str:
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        iterations,
    )
    return dk.hex()


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    try:
        candidate = hash_password(password, salt)
        return hmac.compare_digest(candidate, password_hash)
    except Exception:
        return False


def new_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
