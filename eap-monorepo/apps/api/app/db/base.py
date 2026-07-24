"""SQLAlchemy engine, session factory, and declarative base."""
from __future__ import annotations

from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Root declarative base for all ORM models."""


_engine = None
_SessionLocal = None


def _init_engine() -> None:
    global _engine, _SessionLocal
    if _engine is not None:
        return
    settings = get_settings()
    _engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        future=True,
    )
    _SessionLocal = sessionmaker(
        bind=_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )


def get_engine() -> Any:
    _init_engine()
    return _engine


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a session, commits/rolls back around it."""
    _init_engine()
    assert _SessionLocal is not None
    db = _SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
