"""/api/auth routes."""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session as DbSession

from app.config import get_settings
from app.db import get_session
from app.models import User
from app.services import auth as auth_service
from app.services.deps import LoginRequest, RegisterRequest, UserPublic, require_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _registration_allowed(payload: RegisterRequest) -> bool:
    settings = get_settings()
    if settings.EAP_ENABLE_REGISTRATION:
        return True
    if settings.EAP_BOOTSTRAP_TOKEN and payload.bootstrap_token == settings.EAP_BOOTSTRAP_TOKEN:
        return True
    return False


@router.post("/register", response_model=UserPublic, status_code=201)
def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: DbSession = Depends(get_session),
):
    # First user always registers (and becomes admin)
    is_first_user = db.query(User).count() == 0

    if not is_first_user and not _registration_allowed(payload):
        raise HTTPException(403, "Registration is closed. Contact an administrator.")

    role = "admin" if is_first_user else "user"
    user = auth_service.create_user(
        db,
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
        role=role,
    )

    token = auth_service.create_session(
        db,
        user_id=user.id,
        user_agent=request.headers.get("user-agent"),
        ip_hash=auth_service.hash_ip(request.client.host if request.client else None),
    )
    auth_service.set_session_cookie(response, token)
    return UserPublic.from_user(user)


@router.post("/login", response_model=UserPublic)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: DbSession = Depends(get_session),
):
    user = auth_service.get_user_by_email(db, payload.email)

    if user is None:
        # Burn similar CPU to avoid trivial user enumeration timing
        auth_service.verify_password(
            "$argon2id$v=19$m=65536,t=3,p=2$YWFhYWFhYWFhYWFhYWFhYQ$"
            "Gxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            payload.password,
        )
        raise HTTPException(401, "Invalid credentials.")

    if user.disabled_at:
        raise HTTPException(403, "Account disabled.")

    if not auth_service.verify_password(user.password_hash, payload.password):
        raise HTTPException(401, "Invalid credentials.")

    if auth_service.needs_rehash(user.password_hash):
        user.password_hash = auth_service.hash_password(payload.password)
        db.flush()

    token = auth_service.create_session(
        db,
        user_id=user.id,
        user_agent=request.headers.get("user-agent"),
        ip_hash=auth_service.hash_ip(request.client.host if request.client else None),
    )
    auth_service.set_session_cookie(response, token)
    return UserPublic.from_user(user)


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    _user: User = Depends(require_user),
    db: DbSession = Depends(get_session),
):
    token = getattr(request.state, "session_token", None)
    if token:
        auth_service.revoke_session(db, token)
    auth_service.clear_session_cookie(response)
    return Response(status_code=204)


@router.post("/logout-all", status_code=204)
def logout_all(
    response: Response,
    user: User = Depends(require_user),
    db: DbSession = Depends(get_session),
):
    auth_service.revoke_all_user_sessions(db, user.id)
    auth_service.clear_session_cookie(response)
    return Response(status_code=204)


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(require_user)):
    return UserPublic.from_user(user)
