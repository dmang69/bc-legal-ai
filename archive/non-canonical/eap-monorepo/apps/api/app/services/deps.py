"""Auth FastAPI dependency and request/response schemas."""
from __future__ import annotations

from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session as DbSession

from app.db import get_session
from app.models import User
from app.services import auth as auth_service


class UserPublic(BaseModel):
    id: int
    email: str
    display_name: str
    role: str

    @classmethod
    def from_user(cls, user: User) -> "UserPublic":
        return cls(
            id=user.id, email=user.email,
            display_name=user.display_name, role=user.role,
        )


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=auth_service.MIN_PASSWORD_LENGTH, max_length=200)
    display_name: str = Field(min_length=1, max_length=100)
    bootstrap_token: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def require_user(
    request: Request,
    db: DbSession = Depends(get_session),
    session_token: Optional[str] = Cookie(
        default=None, alias=auth_service.SESSION_COOKIE_NAME
    ),
) -> User:
    if not session_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required.")

    session = auth_service.lookup_session(db, session_token)
    if not session:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session invalid or expired.")

    user = db.get(User, session.user_id)
    if not user:
        auth_service.revoke_session(db, session_token)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session invalid.")
    if user.disabled_at:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled.")

    # Stash the token on the request state so /logout can revoke it without re-parsing
    request.state.session_token = session_token
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin role required.")
    return user


def optional_user(
    request: Request,
    db: DbSession = Depends(get_session),
    session_token: Optional[str] = Cookie(
        default=None, alias=auth_service.SESSION_COOKIE_NAME
    ),
) -> Optional[User]:
    if not session_token:
        return None
    try:
        return require_user(request, db, session_token)
    except HTTPException:
        return None
