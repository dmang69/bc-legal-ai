"""Org AI admin: quotas, allowlists, telemetry."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("ALA_SQLITE_PATH", str(tmp_path / "org.sqlite3"))
    monkeypatch.delenv("ALA_POSTGRES_URL", raising=False)
    monkeypatch.delenv("APP_MODE", raising=False)
    monkeypatch.setenv("ALA_RATE_LIMIT_DISABLED", "1")

    import backend.db.connection as conn_mod
    import backend.identity.service as id_mod
    import backend.audit.ledger as aud_mod
    import backend.platform.matters as mat_mod
    import backend.platform.conversation as chat_mod

    conn_mod._initialized = False
    id_mod._svc = None
    aud_mod._ledger = None
    mat_mod._store = None
    chat_mod._svc = None

    from backend.api.main import app

    with TestClient(app) as c:
        yield c


def _auth(client: TestClient) -> dict[str, str]:
    r = client.post(
        "/v1/platform/auth/register",
        json={
            "org_name": "Admin Firm",
            "email": "orgadmin@synthetic.invalid",
            "password": "securepass99",
        },
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_settings_and_telemetry(client: TestClient):
    h = _auth(client)
    g = client.get("/v1/platform/org/ai/settings", headers=h)
    assert g.status_code == 200
    assert "safe_local" in g.json()["allowed_providers"]

    u = client.put(
        "/v1/platform/org/ai/settings",
        headers=h,
        json={
            "daily_request_quota": 50,
            "allowed_providers": ["safe_local", "ollama"],
            "allow_external_llm": False,
        },
    )
    assert u.status_code == 200, u.text
    assert u.json()["daily_request_quota"] == 50

    # generate usage via complete
    c = client.post(
        "/v1/platform/ai/complete",
        headers=h,
        json={"messages": [{"role": "user", "content": "hi"}], "provider": "safe_local"},
    )
    assert c.status_code == 200

    t = client.get("/v1/platform/org/ai/telemetry", headers=h)
    assert t.status_code == 200
    assert t.json()["daily"] or t.json()["recent"]


def test_quota_blocks_disallowed_provider(client: TestClient):
    h = _auth(client)
    client.put(
        "/v1/platform/org/ai/settings",
        headers=h,
        json={"allowed_providers": ["safe_local"]},
    )
    q = client.get("/v1/platform/org/ai/quota?provider=openai", headers=h)
    assert q.status_code == 200
    assert q.json()["allowed"] is False
