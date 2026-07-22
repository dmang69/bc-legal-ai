"""Connection factory for modular monolith storage."""

from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional

_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_SQLITE = _ROOT / "data" / "ala_platform.sqlite3"
_lock = threading.RLock()
_initialized = False


def get_db_backend() -> str:
    url = os.environ.get("ALA_POSTGRES_URL", "").strip()
    if url:
        return "postgres"
    return "sqlite"


def _sqlite_path() -> Path:
    raw = os.environ.get("ALA_SQLITE_PATH", "").strip()
    return Path(raw) if raw else _DEFAULT_SQLITE


def _connect_sqlite() -> sqlite3.Connection:
    path = _sqlite_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _connect_postgres():
    import psycopg
    from psycopg.rows import dict_row

    url = os.environ["ALA_POSTGRES_URL"]
    conn = psycopg.connect(url, row_factory=dict_row)
    return conn


@contextmanager
def get_connection() -> Iterator[Any]:
    backend = get_db_backend()
    if backend == "postgres":
        conn = _connect_postgres()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        conn = _connect_sqlite()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def init_db(*, force: bool = False) -> str:
    """Apply migrations once per process (or when force=True). Returns backend name."""
    global _initialized
    with _lock:
        if _initialized and not force:
            return get_db_backend()
        from backend.db.migrate import apply_migrations

        apply_migrations()
        _initialized = True
        return get_db_backend()
