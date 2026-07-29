"""HttpOnly session cookies + double-submit CSRF for browser clients.

API clients may continue using Authorization: Bearer (CSRF not required).
Browser clients should use credentials: 'include' and send X-CSRF-Token.
"""

from __future__ import annotations

import os
import secrets
from typing import Optional

from fastapi import Request, Response
from starlette.responses import JSONResponse

SESSION_COOKIE = os.environ.get("ALA_SESSION_COOKIE", "ala_session")
CSRF_COOKIE = os.environ.get("ALA_CSRF_COOKIE", "ala_csrf")
CSRF_HEADER = "X-CSRF-Token"

# Secure cookies when not clearly local
def _cookie_secure() -> bool:
    mode = os.environ.get("APP_MODE", "development").strip().lower()
    if mode in ("development", "test", "public_demo"):
        return False
    return os.environ.get("ALA_COOKIE_SECURE", "1").strip() not in ("0", "false", "no")


def _cookie_samesite() -> str:
    return os.environ.get("ALA_COOKIE_SAMESITE", "lax")


def issue_session_cookies(response: Response, *, token: str, csrf: Optional[str] = None) -> str:
    """Set HttpOnly session cookie and non-HttpOnly CSRF cookie. Returns csrf token."""
    csrf_token = csrf or secrets.token_urlsafe(32)
    secure = _cookie_secure()
    samesite = _cookie_samesite()
    max_age = int(os.environ.get("ALA_SESSION_MAX_AGE", str(12 * 3600)))
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=max_age,
        path="/",
    )
    response.set_cookie(
        key=CSRF_COOKIE,
        value=csrf_token,
        httponly=False,
        secure=secure,
        samesite=samesite,
        max_age=max_age,
        path="/",
    )
    return csrf_token


def clear_session_cookies(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")


def extract_session_token(
    request: Request,
    *,
    authorization: Optional[str] = None,
) -> Optional[str]:
    """Prefer Authorization bearer; fall back to session cookie."""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        if token:
            return token
    cookie = request.cookies.get(SESSION_COOKIE)
    if cookie:
        return cookie.strip() or None
    return None


def auth_via_cookie(request: Request, authorization: Optional[str]) -> bool:
    """True when session is from cookie (not Authorization header)."""
    if authorization and authorization.lower().startswith("bearer ") and authorization.split(" ", 1)[1].strip():
        return False
    return bool(request.cookies.get(SESSION_COOKIE))


def require_csrf_if_cookie_session(request: Request, authorization: Optional[str] = None) -> None:
    """For cookie-authenticated mutating requests, require matching CSRF header.

    Safe methods (GET/HEAD/OPTIONS) skip CSRF. Bearer-auth clients skip CSRF.
    """
    if request.method.upper() in ("GET", "HEAD", "OPTIONS"):
        return
    if not auth_via_cookie(request, authorization):
        return
    cookie_csrf = request.cookies.get(CSRF_COOKIE) or ""
    header_csrf = request.headers.get(CSRF_HEADER) or request.headers.get("x-csrf-token") or ""
    if not cookie_csrf or not header_csrf or not secrets.compare_digest(cookie_csrf, header_csrf):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="CSRF validation failed")


def json_with_session(body: dict, *, token: str, status_code: int = 200) -> JSONResponse:
    """Build JSONResponse that also sets session cookies (token still in body for API clients)."""
    resp = JSONResponse(content=body, status_code=status_code)
    csrf = issue_session_cookies(resp, token=token)
    # Expose csrf for SPA convenience without forcing cookie-only clients
    if isinstance(body, dict):
        # Mutate a copy already serialized — re-build with csrf field
        enriched = dict(body)
        enriched["csrf_token"] = csrf
        resp = JSONResponse(content=enriched, status_code=status_code)
        issue_session_cookies(resp, token=token, csrf=csrf)
    return resp
