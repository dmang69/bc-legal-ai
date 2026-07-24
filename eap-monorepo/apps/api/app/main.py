"""Enterprise AI Platform — FastAPI entry point.

This module wires together:
    - CORS with explicit origins (no wildcard when credentials=true)
    - Auth router (/api/auth/*)
    - Workspace router (/api/*)
    - A single unauthenticated /api/health endpoint for liveness probes
    - Startup seeding of default shared prompts

Templates are gone — the web UI is now Next.js in apps/web. This service
is API-only.
"""
from __future__ import annotations

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import get_settings
from app.db import get_engine
from app.models import Prompt
from app.routers.auth import router as auth_router
from app.routers.workspace import router as workspace_router

# Basic structured logging to stdout so container platforms can collect it
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("app")


def seed_default_prompts() -> int:
    """Seed default shared prompts if the table is empty. Returns count seeded."""
    from sqlalchemy.orm import Session
    engine = get_engine()
    with Session(engine) as db:
        existing = db.scalar(select(Prompt).limit(1))
        if existing is not None:
            return 0
        for title, body in _DEFAULT_PROMPTS:
            db.add(Prompt(owner_user_id=None, title=title, body=body, scope="shared"))
        db.commit()
        return len(_DEFAULT_PROMPTS)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Enterprise AI Platform API",
        version="0.2.0",
        description="Auth + workspace API for the enterprise AI platform.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    app.include_router(auth_router)
    app.include_router(workspace_router)

    @app.get("/api/health", tags=["health"])
    def health():
        """Unauth liveness probe. Does not touch the DB."""
        return {"ok": True, "service": "eap-api", "version": app.version}

    @app.on_event("startup")
    def on_startup() -> None:
        log.info("Starting Enterprise AI Platform API v%s (%s)",
                 app.version, settings.ENVIRONMENT)
        seeded = seed_default_prompts()
        if seeded:
            log.info("Seeded %d default shared prompts", seeded)

    return app


_DEFAULT_PROMPTS = [
    ("Legal issue matrix",
     "Organize the problem into Facts, Assumptions, Issues, Governing Law, "
     "Evidence Gaps, Counterarguments, and Requested Remedy."),
    ("Case chronology",
     "Turn the record into a clean chronology with date, event, source, "
     "and why it matters."),
    ("Code review",
     "Review the code for correctness, security, maintainability, and testing gaps."),
]


app = create_app()
