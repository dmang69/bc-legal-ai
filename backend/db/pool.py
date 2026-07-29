"""Optional PostgreSQL connection pool for multi-worker deployments.

Uses psycopg_pool when installed; falls back to single connections.
SQLite remains process-local (single-writer) — use Postgres for multi-worker.
"""

from __future__ import annotations

import os
import threading
from typing import Any

_pool: Any = None
_pool_lock = threading.Lock()
_pool_failed = False


def pool_enabled() -> bool:
    if os.environ.get("ALA_PG_POOL", "1").strip().lower() in ("0", "false", "no"):
        return False
    return bool(os.environ.get("ALA_POSTGRES_URL", "").strip())


def get_pg_pool():
    """Return a shared ConnectionPool or None if unavailable."""
    global _pool, _pool_failed
    if not pool_enabled() or _pool_failed:
        return None
    if _pool is not None:
        return _pool
    with _pool_lock:
        if _pool is not None:
            return _pool
        try:
            from psycopg_pool import ConnectionPool
            from psycopg.rows import dict_row

            url = os.environ["ALA_POSTGRES_URL"]
            min_size = int(os.environ.get("ALA_PG_POOL_MIN", "1"))
            max_size = int(os.environ.get("ALA_PG_POOL_MAX", "10"))
            _pool = ConnectionPool(
                conninfo=url,
                min_size=min_size,
                max_size=max_size,
                kwargs={"row_factory": dict_row},
                open=True,
            )
            return _pool
        except Exception:
            _pool_failed = True
            return None


def close_pg_pool() -> None:
    global _pool, _pool_failed
    with _pool_lock:
        if _pool is not None:
            try:
                _pool.close()
            except Exception:
                pass
            _pool = None
        _pool_failed = False


def pool_status() -> dict[str, Any]:
    p = get_pg_pool()
    if p is None:
        return {"enabled": False, "backend": "none"}
    try:
        return {
            "enabled": True,
            "min_size": getattr(p, "min_size", None),
            "max_size": getattr(p, "max_size", None),
        }
    except Exception as e:
        return {"enabled": True, "error": str(e)}
