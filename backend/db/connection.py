"""Connection factory for modular monolith storage.

- SQLite: default local file (single-writer; fine for dev / single process)
- Postgres: ALA_POSTGRES_URL — multi-worker safe when used with pool + uvicorn workers
"""

from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from backend.db.compat import CompatCursor

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
    conn = sqlite3.connect(str(path), check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # Better concurrent read behaviour under multi-thread single process
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _connect_postgres_raw():
    import psycopg
    from psycopg.rows import dict_row

    from backend.db.pool import get_pg_pool

    pool = get_pg_pool()
    if pool is not None:
        # Caller must return connection to pool via context manager below
        return pool.connection(), True
    url = os.environ["ALA_POSTGRES_URL"]
    return psycopg.connect(url, row_factory=dict_row), False


@contextmanager
def get_connection() -> Iterator[Any]:
    backend = get_db_backend()
    if backend == "postgres":
        pooled = False
        try:
            raw, pooled = _connect_postgres_raw()
        except Exception:
            # raw may be a context manager from pool
            raise
        if pooled:
            # pool.connection() returns a context manager in psycopg_pool 3.x
            with raw as conn:
                wrapped = CompatCursor(conn, dialect="postgres")
                try:
                    yield wrapped
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise
        else:
            conn = raw
            wrapped = CompatCursor(conn, dialect="postgres")
            try:
                yield wrapped
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
    else:
        conn = _connect_sqlite()
        wrapped = CompatCursor(conn, dialect="sqlite")
        try:
            yield wrapped
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


def multi_worker_ready() -> dict[str, Any]:
    """Report whether this process is configured for multi-worker API hosts."""
    backend = get_db_backend()
    from backend.db.pool import pool_status

    return {
        "backend": backend,
        "multi_worker_supported": backend == "postgres",
        "sqlite_single_writer_only": backend == "sqlite",
        "pool": pool_status() if backend == "postgres" else {"enabled": False},
        "guidance": (
            "Set ALA_POSTGRES_URL and run uvicorn with --workers N. "
            "Do not use SQLite with multiple workers."
            if backend == "sqlite"
            else "Postgres configured; use ConnectionPool (ALA_PG_POOL=1) for multi-worker."
        ),
    }
