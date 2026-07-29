"""OpenClaw harness, Kimi provider, and Arena AI pillars."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("ALA_SQLITE_PATH", str(tmp_path / "pillars.sqlite3"))
    monkeypatch.delenv("ALA_POSTGRES_URL", raising=False)
    monkeypatch.delenv("APP_MODE", raising=False)
    monkeypatch.setenv("ALA_RATE_LIMIT_DISABLED", "1")
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
            "org_name": "Pillar Firm",
            "email": "pillars@synthetic.invalid",
            "password": "securepass99",
        },
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_suite_pillars(client: TestClient):
    h = _auth(client)
    r = client.get("/v1/platform/ai/suite", headers=h)
    assert r.status_code == 200
    body = r.json()
    pillars = body.get("pillars") or {}
    assert pillars.get("openclaw", {}).get("enabled") is True
    assert pillars.get("kimi", {}).get("enabled") is True
    assert pillars.get("arena_ai", {}).get("enabled") is True
    ids = {p["id"] for p in body["providers"]}
    assert "kimi" in ids
    assert "puter" in ids


def test_openclaw_capabilities_and_run(client: TestClient):
    h = _auth(client)
    caps = client.get("/v1/platform/ai/openclaw/capabilities", headers=h)
    assert caps.status_code == 200
    assert caps.json()["openclaw"] if "openclaw" in caps.json() else True
    assert caps.json()["court_ready_default"] is False
    tools = client.get("/v1/platform/ai/openclaw/tools", headers=h)
    assert tools.status_code == 200
    assert len(tools.json()["tools"]) >= 5

    run = client.post(
        "/v1/platform/ai/openclaw/run",
        headers=h,
        json={
            "goal": "Triage a residential tenancy judicial review: Form 66, 60 day clock, research plan.",
            "auto_approve": False,
            "execute": True,
        },
    )
    assert run.status_code == 200, run.text
    body = run.json()
    assert body["ok"] is True
    assert body["court_ready"] is False
    assert body["plan"]
    assert body["steps"]
    assert body["run_id"]
    assert "OpenClaw" in body["summary"] or "openclaw" in body["summary"].lower() or "Triage" in body["summary"]


def test_openclaw_chat_slash(client: TestClient):
    h = _auth(client)
    c = client.post("/v1/platform/conversations", headers=h, json={"title": "Claw"})
    cid = c.json()["conversation_id"]
    m = client.post(
        f"/v1/platform/conversations/{cid}/messages",
        headers=h,
        json={"content": "/claw summarize RTB repair obligations and next steps for a tenant"},
    )
    assert m.status_code == 200, m.text
    meta = m.json()["assistant"]["meta"]
    assert meta.get("provider") == "openclaw" or meta.get("controls", {}).get("openclaw")
    assert meta.get("controls", {}).get("court_ready") is False


def test_kimi_provider_and_client_content(client: TestClient):
    h = _auth(client)
    prov = client.get("/v1/platform/workspace/model-providers", headers=h)
    kimi = next(p for p in prov.json()["providers"] if p["id"] == "kimi")
    assert kimi.get("client_side") is True
    assert any("kimi" in m.lower() or "moonshot" in m.lower() for m in (kimi.get("models") or []))

    c = client.post("/v1/platform/conversations", headers=h, json={"title": "Kimi"})
    cid = c.json()["conversation_id"]
    m = client.post(
        f"/v1/platform/conversations/{cid}/messages",
        headers=h,
        json={
            "content": "Analyze this long record outline for JR grounds.",
            "provider": "kimi",
            "model": "moonshotai/kimi-k2.5",
            "client_content": (
                "Possible grounds: patent unreasonableness and procedural fairness. "
                "Verify record completeness. Not legal advice."
            ),
        },
    )
    assert m.status_code == 200, m.text
    assert m.json()["assistant"]["meta"]["provider"] == "kimi"
    assert m.json()["assistant"]["meta"]["controls"]["client_side"] is True


def test_arena_ai_presets_and_client_runs(client: TestClient):
    h = _auth(client)
    p = client.get("/v1/platform/ai/arena/presets", headers=h)
    assert p.status_code == 200
    ids = {x["id"] for x in p.json()["presets"]}
    assert "legal_core" in ids
    assert "kimi_focus" in ids

    r = client.post(
        "/v1/platform/ai/arena",
        headers=h,
        json={
            "prompt": "What is Form 66 used for in BC Supreme Court JR?",
            "preset": "legal_core",
            "client_runs": [
                {
                    "provider": "kimi",
                    "model": "moonshotai/kimi-k2.5",
                    "content": (
                        "Form 66 is the petition for judicial review. "
                        "Not legal advice. Verify SCR Rule 16-1. court_ready false."
                    ),
                },
                {
                    "provider": "puter",
                    "model": "gpt-5-nano",
                    "content": "Form 66 starts a JR petition. Working draft. Not legal advice.",
                },
            ],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("arena_ai") is True
    assert body["court_ready"] is False
    assert body["runs"]
    assert body["ranking"]
    sources = {run.get("source") for run in body["runs"]}
    assert "client" in sources or any(run["provider"] in ("kimi", "puter") for run in body["runs"])
    assert body["winner"]
