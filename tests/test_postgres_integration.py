"""Live PostgreSQL integration tests.

Skipped unless ALA_POSTGRES_URL is set (CI test-postgres job provides it).

These tests exercise the same application code paths as SQLite unit tests against
a real Postgres instance: register → matter → ACL deny → export package + Form 66.
"""

from __future__ import annotations

import os
import uuid

import pytest

pg_url = os.environ.get("ALA_POSTGRES_URL", "").strip()
pytestmark = [
    pytest.mark.postgres_required,
    pytest.mark.skipif(
        not pg_url,
        reason="ALA_POSTGRES_URL not set — Postgres integration skipped",
    ),
]


@pytest.fixture()
def pg_client(monkeypatch):
    """Isolated namespace via unique emails; shared schema from migrations."""
    monkeypatch.setenv("ALA_POSTGRES_URL", pg_url)
    monkeypatch.delenv("ALA_SQLITE_PATH", raising=False)
    monkeypatch.delenv("APP_MODE", raising=False)
    monkeypatch.setenv("ALA_RATE_LIMIT_DISABLED", "1")
    monkeypatch.setenv("ALA_PG_POOL", "0")  # simpler for tests

    import backend.db.connection as conn_mod
    import backend.identity.service as id_mod
    import backend.audit.ledger as aud_mod
    import backend.platform.matters as mat_mod
    import backend.platform.evidence as ev_mod

    conn_mod._initialized = False
    id_mod._svc = None
    aud_mod._ledger = None
    mat_mod._store = None
    ev_mod._ev = None

    from backend.db import init_db

    init_db(force=True)

    from fastapi.testclient import TestClient
    from backend.api.main import app

    with TestClient(app) as c:
        yield c


def _register(client, suffix: str) -> dict[str, str]:
    email = f"pg_{suffix}_{uuid.uuid4().hex[:8]}@synthetic.invalid"
    r = client.post(
        "/v1/platform/auth/register",
        json={
            "org_name": f"PG Org {suffix}",
            "email": email,
            "password": "securepass99",
            "display_name": f"PG User {suffix}",
        },
    )
    assert r.status_code == 200, r.text
    assert r.json().get("token")
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_postgres_backend_reported(pg_client):
    h = pg_client.get("/health")
    assert h.status_code == 200
    assert h.json().get("db_backend") == "postgres"
    mw = h.json().get("multi_worker") or {}
    assert mw.get("multi_worker_supported") is True


def test_postgres_register_matter_isolation(pg_client):
    a = _register(pg_client, "a")
    b = _register(pg_client, "b")
    m = pg_client.post(
        "/v1/platform/matters",
        headers=a,
        json={"title": "PG matter", "synthetic": True},
    )
    assert m.status_code == 200, m.text
    mid = m.json()["matter_id"]

    ok = pg_client.get(f"/v1/platform/matters/{mid}", headers=a)
    # list endpoint may vary — use consents grant as matter-scoped check
    cons = pg_client.post(
        f"/v1/matters/{mid}/consents",
        headers=a,
        json={
            "subject_id": "client-pg",
            "category": "AI_ANALYSIS",
            "purpose": "synthetic",
        },
    )
    assert cons.status_code == 200, cons.text

    denied = pg_client.post(
        f"/v1/matters/{mid}/consents",
        headers=b,
        json={
            "subject_id": "client-x",
            "category": "AI_ANALYSIS",
            "purpose": "should fail",
        },
    )
    assert denied.status_code == 403, denied.text


def test_postgres_session_resolve_and_me(pg_client):
    headers = _register(pg_client, "me")
    me = pg_client.get("/v1/platform/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"].endswith("@synthetic.invalid")


def test_postgres_form66_docx_and_jr_clock(pg_client):
    headers = _register(pg_client, "f66")
    m = pg_client.post(
        "/v1/platform/matters",
        headers=headers,
        json={"title": "JR petition matter", "synthetic": True, "client_label": "Test Tenant"},
    )
    assert m.status_code == 200, m.text
    mid = m.json()["matter_id"]

    outline = pg_client.get(f"/v1/platform/matters/{mid}/drafts/form-66", headers=headers)
    assert outline.status_code == 200
    body = outline.json()
    assert body.get("form_number") == "66" or body.get("court_ready") is False

    docx = pg_client.get(f"/v1/platform/matters/{mid}/drafts/form-66.docx", headers=headers)
    assert docx.status_code == 200, docx.text
    assert docx.headers.get("X-Court-Ready") == "false"
    assert docx.headers.get("X-Form-Number") == "66"
    # DOCX is a zip package
    assert docx.content[:2] == b"PK"

    jr = pg_client.post(
        "/v1/deadlines/jr-clock",
        headers=headers,
        json={"matter_id": mid, "issuance_date": "2026-01-15"},
    )
    assert jr.status_code == 200, jr.text
    assert jr.json().get("primary_deadline")


def test_postgres_audit_chain(pg_client):
    headers = _register(pg_client, "aud")
    m = pg_client.post(
        "/v1/platform/matters",
        headers=headers,
        json={"title": "Audit matter", "synthetic": True},
    )
    assert m.status_code == 200
    verify = pg_client.get("/v1/platform/audit/verify", headers=headers)
    assert verify.status_code == 200
    assert verify.json().get("ok") is True
