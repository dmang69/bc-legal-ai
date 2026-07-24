"""Shared FastAPI dependencies using Annotated type hints (PEP 593).

Usage:
    from backend.api.dependencies import CurrentUser

    @router.get("/some-route")
    def my_route(current_user: CurrentUser):
        ...  # current_user is a UserInfo instance
"""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException

from backend.identity import AuthError, UserInfo, get_identity_service


async def resolve_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
) -> UserInfo:
    """Extract and validate the bearer token from the Authorization header.

    Returns:
        UserInfo: The authenticated user.

    Raises:
        HTTPException 401: If the token is missing, malformed, expired, or revoked.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Bearer token required")
    try:
        return get_identity_service().resolve_token(token)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


# Reusable Annotated type alias for dependency injection.
# Inject into any FastAPI route handler that requires authentication:
#
#   @router.get("/matters")
#   def list_matters(current_user: CurrentUser):
#       ...
#
CurrentUser = Annotated[UserInfo, Depends(resolve_current_user)]


def require_matter_access(
    user: UserInfo,
    matter_id: str,
    *,
    min_level: str = "read",
) -> str:
    """Require deny-first access to an org-scoped matter.

    Ethical walls and revoked memberships are enforced inside the identity
    service before owner/admin role grants are considered.
    """
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
    authorization: Annotated[Optional[str], Header()] = None,
) -> str:
    """Extract the raw bearer token string from the Authorization header.

    This is useful for operations like session revocation where the raw
    token string is needed rather than just the resolved UserInfo.

    Returns:
        str: The raw bearer token string.

    Raises:
        HTTPException 401: If the token is missing or malformed.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Bearer token required")
    return token


# Annotated type alias for the raw bearer token string.
RawBearerToken = Annotated[str, Depends(resolve_bearer_token)]

