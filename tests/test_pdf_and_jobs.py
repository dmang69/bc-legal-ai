"""PDF extract + job queue unit tests."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _db(monkeypatch, tmp_path):
    monkeypatch.setenv("ALA_SQLITE_PATH", str(tmp_path / "j.sqlite3"))
    monkeypatch.delenv("ALA_POSTGRES_URL", raising=False)
    import backend.db.connection as c

    c._initialized = False
    from backend.db import init_db

    init_db(force=True)
    yield


def test_pdf_extract_non_pdf():
    from backend.platform.pdf_extract import extract_pdf_bytes

    r = extract_pdf_bytes(b"not a pdf")
    assert r.ok is False


def test_job_queue():
    from backend.platform import jobs

    jid = jobs.enqueue("echo", {"x": 1}, matter_id="m1")
    out = jobs.run_next({"echo": lambda p: {"echoed": p["x"]}})
    assert out is not None
    assert out["status"] == "DONE"
    assert out["result"]["echoed"] == 1
    got = jobs.get_job(jid)
    assert got["status"] == "DONE"
