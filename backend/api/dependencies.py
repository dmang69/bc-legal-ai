"""Shared FastAPI dependencies using Annotated type hints (PEP 593).

Usage:
    from backend.api.dependencies import CurrentUser

    @router.get("/some-route")
    def my_route(current_user: CurrentUser):
        ...  # current_user is a UserInfo instance
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, Request

from backend.api.session_cookies import (
    extract_session_token,
    require_csrf_if_cookie_session,
)
from backend.identity import AuthError, UserInfo, get_identity_service


async def resolve_current_user(
    request: Request,
    authorization: Annotated[Optional[str], Header()] = None,
) -> UserInfo:
    """Resolve user from Authorization: Bearer or HttpOnly session cookie.

    Cookie-authenticated mutating requests also require CSRF header.
    """
    require_csrf_if_cookie_session(request, authorization)
    token = extract_session_token(request, authorization=authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Bearer token or session cookie required")
    try:
        return get_identity_service().resolve_token(token)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


# Reusable Annotated type alias for dependency injection.
CurrentUser = Annotated[UserInfo, Depends(resolve_current_user)]


def require_matter_access(
    user: UserInfo,
    matter_id: str,
    *,
    min_level: str = "read",
) -> str:
    """Require deny-first access to an org-scoped matter."""
    if not matter_id:
        raise HTTPException(status_code=400, detail="matter_id required")
    if not get_identity_service().can_access_matter(user, matter_id, min_level=min_level):
        raise HTTPException(status_code=403, detail="Matter access denied")
    return matter_id


def require_optional_matter_access(
    user: UserInfo,
    matter_id: str = "",
    *,
    min_level: str = "read",
) -> str:
    """Require matter access when a matter_id is supplied."""
    if matter_id:
        return require_matter_access(user, matter_id, min_level=min_level)
    return ""


async def resolve_bearer_token(
    request: Request,
    authorization: Annotated[Optional[str], Header()] = None,
) -> str:
    """Raw session token from bearer header or cookie (for logout/revoke)."""
    token = extract_session_token(request, authorization=authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Bearer token or session cookie required")
    return token


RawBearerToken = Annotated[str, Depends(resolve_bearer_token)]
