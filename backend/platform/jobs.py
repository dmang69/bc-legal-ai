"""In-process job queue stub (M2 workers) — Redis later; SQLite table now."""

from __future__ import annotations

import json
import uuid
from typing import Any, Callable, Optional

from backend.db import get_connection, init_db

# Extend schema on first use
_JOBS_DDL = """
CREATE TABLE IF NOT EXISTS background_jobs (
  job_id TEXT PRIMARY KEY,
  job_type TEXT NOT NULL,
  matter_id TEXT NOT NULL DEFAULT '',
  payload TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'PENDING',
  result TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  started_at TEXT,
  finished_at TEXT
);
"""


def _ensure() -> None:
    init_db()
    with get_connection() as conn:
        conn.executescript(_JOBS_DDL)


def enqueue(job_type: str, payload: dict[str, Any], *, matter_id: str = "") -> str:
    _ensure()
    job_id = f"job_{uuid.uuid4().hex[:14]}"
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO background_jobs (job_id, job_type, matter_id, payload, status)
            VALUES (?, ?, ?, ?, 'PENDING')
            """,
            (job_id, job_type, matter_id, json.dumps(payload)),
        )
    return job_id


def run_next(handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]]) -> Optional[dict[str, Any]]:
    _ensure()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM background_jobs WHERE status = 'PENDING'
            ORDER BY created_at ASC LIMIT 1
            """
        ).fetchone()
        if not row:
            return None
        job_id = row["job_id"]
        conn.execute(
            "UPDATE background_jobs SET status = 'RUNNING', started_at = datetime('now') WHERE job_id = ?",
            (job_id,),
        )
        payload = json.loads(row["payload"] or "{}")
        handler = handlers.get(row["job_type"])
        try:
            if not handler:
                raise ValueError(f"No handler for {row['job_type']}")
            result = handler(payload)
            conn.execute(
                """
                UPDATE background_jobs SET status = 'DONE', result = ?, finished_at = datetime('now')
                WHERE job_id = ?
                """,
                (json.dumps(result), job_id),
            )
            return {"job_id": job_id, "status": "DONE", "result": result}
        except Exception as e:
            conn.execute(
                """
                UPDATE background_jobs SET status = 'FAILED', result = ?, finished_at = datetime('now')
                WHERE job_id = ?
                """,
                (json.dumps({"error": str(e)}), job_id),
            )
            return {"job_id": job_id, "status": "FAILED", "error": str(e)}


def get_job(job_id: str) -> Optional[dict[str, Any]]:
    _ensure()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT job_id, job_type, status, result, matter_id FROM background_jobs WHERE job_id = ?",
            (job_id,),
        ).fetchone()
    if not row:
        return None
    return dict(row)
