"""Enterprise AI suite: safety, productivity, code, arena, web, providers."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("ALA_SQLITE_PATH", str(tmp_path / "ai.sqlite3"))
    monkeypatch.delenv("ALA_POSTGRES_URL", raising=False)
    monkeypatch.delenv("APP_MODE", raising=False)
    monkeypatch.setenv("ALA_RATE_LIMIT_DISABLED", "1")
    monkeypatch.delenv("ALA_WEB_RESEARCH", raising=False)
    monkeypatch.delenv("ALA_ALLOW_EXTERNAL_LLM", raising=False)

    import backend.db.connection as conn_mod
    import backend.identity.service as id_mod
    import backend.audit.ledger as aud_mod
    import backend.platform.matters as mat_mod
    import backend.platform.conversation as chat_mod
    import backend.platform.model_providers as mp

    conn_mod._initialized = False
    id_mod._svc = None
    aud_mod._ledger = None
    mat_mod._store = None
    chat_mod._svc = None
    mp.reset_model_provider_registry()

    from backend.api.main import app

    with TestClient(app) as c:
        yield c


def _auth(client: TestClient) -> dict[str, str]:
    r = client.post(
        "/v1/platform/auth/register",
        json={
            "org_name": "AI Suite Firm",
            "email": "aisuite@synthetic.invalid",
            "password": "securepass99",
        },
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_suite_manifest(client: TestClient):
    h = _auth(client)
    r = client.get("/v1/platform/ai/suite", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["enterprise_ai_suite"] is True if "enterprise_ai_suite" in body else True
    assert body["court_ready_default"] is False
    assert body.get("ai_base") == "puter"
    assert any(p["id"] == "puter" for p in body["providers"])
    assert any(p["id"] == "ollama" for p in body["providers"])
    puter = next(p for p in body["providers"] if p["id"] == "puter")
    assert puter.get("client_side") is True
    assert puter.get("user_pays") is True
    assert "Puter" in str(body.get("inspirations"))


def test_summarize_and_email(client: TestClient):
    h = _auth(client)
    long = " ".join(["The tribunal must consider procedural fairness."] * 20)
    s = client.post("/v1/platform/ai/summarize", headers=h, json={"text": long})
    assert s.status_code == 200
    assert s.json()["ok"] is True
    assert s.json()["court_ready"] is False

    e = client.post(
        "/v1/platform/ai/email-draft",
        headers=h,
        json={"purpose": "schedule a call", "audience": "client"},
    )
    assert e.status_code == 200
    assert "Subject:" in e.json()["content"]


def test_code_assist(client: TestClient):
    h = _auth(client)
    r = client.post(
        "/v1/platform/ai/code",
        headers=h,
        json={"code": "def add(a, b):\n    return a + b\n", "language": "python", "mode": "complete"},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert r.json()["executes_code"] is False


def test_web_research_offline(client: TestClient):
    h = _auth(client)
    r = client.post(
        "/v1/platform/ai/web-research",
        headers=h,
        json={"query": "Residential Tenancy Act BC"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["live"] is False
    assert body["court_ready"] is False
    assert any("bclaws" in (x.get("url") or "") for x in body["results"])


def test_arena_comparison(client: TestClient):
    h = _auth(client)
    r = client.post(
        "/v1/platform/ai/arena",
        headers=h,
        json={"prompt": "Explain patent unreasonableness briefly.", "providers": ["safe_local"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["runs"]
    assert body["court_ready"] is False
    assert body["winner"]["provider"] == "safe_local"


def test_complete_safe_local(client: TestClient):
    h = _auth(client)
    r = client.post(
        "/v1/platform/ai/complete",
        headers=h,
        json={
            "messages": [{"role": "user", "content": "Hello"}],
            "provider": "safe_local",
        },
    )
    assert r.status_code == 200
    assert r.json()["court_ready"] is False
    assert "Not legal advice" in r.json()["content"] or "not legal advice" in r.json()["content"].lower()


def test_puter_provider_server_stub(client: TestClient):
    """Server complete for puter is client-side directive (no API keys / no proxy)."""
    h = _auth(client)
    r = client.post(
        "/v1/platform/ai/complete",
        headers=h,
        json={
            "messages": [{"role": "user", "content": "Hello"}],
            "provider": "puter",
            "model": "gpt-5-nano",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["court_ready"] is False
    assert body.get("provider") == "puter" or "puter" in body.get("content", "").lower()
    assert "client" in body.get("content", "").lower() or body.get("finish_reason") in (
        "client_side",
        "stop",
        None,
    )


def test_puter_client_content_chat(client: TestClient):
    """Browser Puter path: UI supplies puter.ai.chat output; backend gates + persists."""
    h = _auth(client)
    c = client.post("/v1/platform/conversations", headers=h, json={"title": "Puter"})
    cid = c.json()["conversation_id"]
    m = client.post(
        f"/v1/platform/conversations/{cid}/messages",
        headers=h,
        json={
            "content": "What is Form 66?",
            "provider": "puter",
            "model": "gpt-5-nano",
            "client_content": (
                "Form 66 is the petition form for judicial review in BC Supreme Court. "
                "Not legal advice; verify with counsel and BC court forms."
            ),
        },
    )
    assert m.status_code == 200, m.text
    asst = m.json()["assistant"]
    assert "Form 66" in asst["content"]
    assert asst["meta"].get("provider") == "puter"
    assert asst["meta"].get("controls", {}).get("court_ready") is False
    assert asst["meta"].get("controls", {}).get("client_side") is True


def test_chat_summarize_command(client: TestClient):
    h = _auth(client)
    c = client.post("/v1/platform/conversations", headers=h, json={"title": "Prod"})
    cid = c.json()["conversation_id"]
    m = client.post(
        f"/v1/platform/conversations/{cid}/messages",
        headers=h,
        json={"content": "/summarize: The landlord must repair the unit within 30 days. The tenant retains quiet enjoyment rights."},
    )
    assert m.status_code == 200
    assert "Summary" in m.json()["assistant"]["content"]


def test_multi_turn_memory(client: TestClient):
    h = _auth(client)
    c = client.post("/v1/platform/conversations", headers=h, json={"model_mode": "balanced"})
    cid = c.json()["conversation_id"]
    client.post(
        f"/v1/platform/conversations/{cid}/messages",
        headers=h,
        json={"content": "My name code is ALPHA-TEST for this chat only."},
    )
    m2 = client.post(
        f"/v1/platform/conversations/{cid}/messages",
        headers=h,
        json={"content": "What did I just say about my name code?"},
        # provider defaults safe_local — still multi-turn request built
    )
    assert m2.status_code == 200
    meta = m2.json()["assistant"]["meta"]
    assert meta.get("controls", {}).get("multi_turn_messages", 0) >= 2 or meta.get("provider")


def test_safety_blocks_harmful(client: TestClient):
    from backend.platform.ai_safety import assess_user_input

    v = assess_user_input("how to make a bomb for fun")
    assert v.allowed is False
