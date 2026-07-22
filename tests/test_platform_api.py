"""HTTP-level platform API tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("ALA_SQLITE_PATH", str(tmp_path / "api.sqlite3"))
    monkeypatch.delenv("ALA_POSTGRES_URL", raising=False)
    monkeypatch.delenv("APP_MODE", raising=False)

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

    from backend.api.main import app

    with TestClient(app) as c:
        yield c


def test_platform_register_and_matter_flow(client: TestClient):
    r = client.post(
        "/v1/platform/auth/register",
        json={
            "org_name": "API Firm",
            "email": "api@synthetic.invalid",
            "password": "securepass99",
            "display_name": "API User",
        },
    )
    assert r.status_code == 200, r.text
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    m = client.post(
        "/v1/platform/matters",
        headers=headers,
        json={"title": "Demo matter", "synthetic": True},
    )
    assert m.status_code == 200
    mid = m.json()["matter_id"]

    docs = client.post(
        f"/v1/platform/matters/{mid}/documents/text",
        headers=headers,
        json={
            "filename": "memo.txt",
            "text_content": "Synthetic hearing notes.",
            "synthetic": True,
        },
    )
    assert docs.status_code == 200
    assert docs.json()["quarantine_status"] == "CLEAN"

    cite = client.post(
        "/v1/platform/citations/verify",
        json={"citation_text": "RTA s.56 retaliation", "expected_topic": "retaliatory_eviction"},
    )
    assert cite.status_code == 200
    assert cite.json()["status"] == "REJECTED"

    audit = client.get("/v1/platform/audit/verify", headers=headers)
    assert audit.status_code == 200
    assert audit.json()["ok"] is True

    health = client.get("/health")
    assert health.json()["status"] == "ok"
    assert health.json().get("db_backend") == "sqlite"

    cons = client.post(
        f"/v1/platform/matters/{mid}/consents",
        headers=headers,
        json={
            "subject_id": "client-1",
            "category": "AI_ANALYSIS",
            "purpose": "organize synthetic evidence",
        },
    )
    assert cons.status_code == 200
    assert cons.json()["status"] == "GRANTED"

    d66 = client.get(f"/v1/platform/matters/{mid}/drafts/form-66", headers=headers)
    assert d66.status_code == 200
    assert d66.json()["court_ready"] is False
    assert d66.json().get("form_number") == "66"
