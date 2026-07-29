"""Database-agnostic helpers for cross-compatible SQL construction.

Provides:
- `now_iso()` — UTC ISO timestamp for parameterized SQL (not SQL function call)
- `interpolate(sql, **kwargs)` — safely interpolate identifiers (not values)
- `compat(sql, dialect)` — future: convert between SQLite `?` and psycopg `%s`

All timestamps should be passed as Python parameters, not via SQL function calls
like `datetime('now')` which are SQLite-specific.
"""

from __future__ import annotations

from datetime import datetime, timezone


def now_iso() -> str:
    """Return UTC ISO-8601 timestamp as a Python string for parameterized SQL.

    Use this instead of SQLite's `datetime('now')` or PostgreSQL's `NOW()`
    to keep SQL dialect-agnostic.

    Example:
        conn.execute("INSERT INTO t (ts) VALUES (?)", (now_iso(),))
    """
    return datetime.now(timezone.utc).isoformat()


def compat_schema_ddl(ddl: str) -> list[str]:
    """Split a multi-statement DDL string into individual statements.

    Replaces the use of `executescript()` which is SQLite-only.
    PostgreSQL's psycopg does not support `executescript()`.

    Example:
        for stmt in compat_schema_ddl(_MY_DDL):
            conn.execute(stmt)
    """
    statements: list[str] = []
    for raw in ddl.split(";"):
        stmt = raw.strip()
        if stmt:
            # Remove DEFAULT (datetime('now')) references from embedded DDL
            stmt = stmt.replace(
                "DEFAULT (datetime('now'))",
                "DEFAULT ''"
            )
            statements.append(stmt)
    return statements


def compat_insert_or_ignore() -> str:
    """Return DB-agnostic INSERT ... ON CONFLICT DO NOTHING clause suffix.

    Works on SQLite 3.24+ and PostgreSQL 9.5+.
    """
    return "ON CONFLICT DO NOTHING"


def wrap_timestamp_defaults(sql: str) -> str:
    """Replace SQLite-specific datetime defaults with empty string defaults.

    SQLite: DEFAULT (datetime('now'))
    PostgreSQL: DEFAULT CURRENT_TIMESTAMP or DEFAULT NOW()

    To keep code cross-compatible, we default to '' and set the value
    from application code via now_iso() parameter.
    """
    replacements = [
        ("DEFAULT (datetime('now'))", "DEFAULT ''"),
        ("DEFAULT datetime('now')", "DEFAULT ''"),
    ]
    result = sql
    for old, new in replacements:
        result = result.replace(old, new)
    return result

