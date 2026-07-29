"""SQL dialect placeholder translation."""

from backend.db.compat import translate_sql


def test_sqlite_unchanged():
    sql = "SELECT * FROM users WHERE email = ? AND org_id = ?"
    assert translate_sql(sql, dialect="sqlite") == sql


def test_postgres_placeholders():
    sql = "SELECT * FROM users WHERE email = ? AND org_id = ?"
    assert translate_sql(sql, dialect="postgres") == (
        "SELECT * FROM users WHERE email = %s AND org_id = %s"
    )


def test_multi_worker_report_sqlite():
    from backend.db.connection import multi_worker_ready

    r = multi_worker_ready()
    assert r["backend"] == "sqlite"
    assert r["multi_worker_supported"] is False
    assert r["sqlite_single_writer_only"] is True
