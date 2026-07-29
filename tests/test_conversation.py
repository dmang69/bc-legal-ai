"""Conversational workspace API tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("ALA_SQLITE_PATH", str(tmp_path / "chat.sqlite3"))
    monkeypatch.delenv("ALA_POSTGRES_URL", raising=False)
    monkeypatch.delenv("APP_MODE", raising=False)

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
            "org_name": "Chat Firm",
            "email": "chat@synthetic.invalid",
            "password": "securepass99",
        },
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_conversation_jr_flow(client: TestClient):
    h = _auth(client)
    c = client.post(
        "/v1/platform/conversations",
        headers=h,
        json={"title": "JR help", "chat_type": "general", "model_mode": "balanced"},
    )
    assert c.status_code == 200
    cid = c.json()["conversation_id"]

    m = client.post(
        f"/v1/platform/conversations/{cid}/messages",
        headers=h,
        json={"content": "Review this RTB decision and identify every ground for judicial review."},
    )
    assert m.status_code == 200
    asst = m.json()["assistant"]
    assert asst["role"] == "assistant"
    assert "Form 66" in asst["content"] or "judicial" in asst["content"].lower()
    assert asst["meta"]["actions"]
    assert any("Not legal advice" in w for w in asst["meta"]["warnings"])


def test_s56_warning_in_chat(client: TestClient):
    h = _auth(client)
    c = client.post(
        "/v1/platform/conversations",
        headers=h,
        json={"chat_type": "research"},
    )
    cid = c.json()["conversation_id"]
    m = client.post(
        f"/v1/platform/conversations/{cid}/messages",
        headers=h,
        json={"content": "Is RTA s.56 a retaliation test?"},
    )
    assert m.status_code == 200
    meta = m.json()["assistant"]["meta"]
    assert any("REJECTED" in w or "s.56" in w for w in meta["warnings"]) or meta.get(
        "citations"
    )


def test_agent_plan(client: TestClient):
    h = _auth(client)
    c = client.post("/v1/platform/conversations", headers=h, json={})
    cid = c.json()["conversation_id"]
    m = client.post(
        f"/v1/platform/conversations/{cid}/messages",
        headers=h,
        json={"content": "Build the complete Book of Authorities for this petition."},
    )
    assert m.status_code == 200
    assert "PLAN" in m.json()["assistant"]["content"]
    assert m.json()["assistant"]["meta"]["work_panel"]["view"] == "agent"


def test_general_chat_ignores_matter_bind(client: TestClient):
    h = _auth(client)
    mat = client.post(
        "/v1/platform/matters",
        headers=h,
        json={"title": "Secret", "synthetic": True},
    )
    mid = mat.json()["matter_id"]
    c = client.post(
        "/v1/platform/conversations",
        headers=h,
        json={"chat_type": "general", "matter_id": mid},
    )
    assert c.status_code == 200
    assert c.json().get("matter_id") in (None, "")
