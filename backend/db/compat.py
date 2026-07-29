"""DB dialect compatibility: SQLite ``?`` placeholders ↔ Postgres ``%s``."""

from __future__ import annotations

import re
from typing import Any, Optional, Sequence


_PLACEHOLDER = re.compile(r"\?")


def translate_sql(sql: str, *, dialect: str) -> str:
    """Translate SQL placeholders for the active dialect.

    Application code uses SQLite-style ``?`` placeholders everywhere.
    PostgreSQL (psycopg) expects ``%s``.
    """
    if dialect == "postgres":
        return _PLACEHOLDER.sub("%s", sql)
    return sql


class CompatCursor:
    """Thin cursor/connection wrapper normalizing execute + row access."""

    def __init__(self, conn: Any, *, dialect: str) -> None:
        self._conn = conn
        self._dialect = dialect

    @property
    def dialect(self) -> str:
        return self._dialect

    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> Any:
        q = translate_sql(sql, dialect=self._dialect)
        if params is None:
            return self._conn.execute(q)
        return self._conn.execute(q, params)

    def executemany(self, sql: str, params_seq: Sequence[Sequence[Any]]) -> Any:
        q = translate_sql(sql, dialect=self._dialect)
        return self._conn.executemany(q, params_seq)

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()

    def close(self) -> None:
        self._conn.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._conn, name)
