"""Skills runtime + chat integration tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_load_skills_catalog():
    from backend.skills_runtime import catalog_summary, clear_skill_cache, load_all_skills, resolve_skills

    clear_skill_cache()
    docs = load_all_skills()
    assert "supreme-court-civil-counsel" in docs
    assert "bc-judicial-review-guide" in docs
    assert docs["bc-judicial-review-guide"].body
    assert "Form 66" in docs["bc-judicial-review-guide"].body

    picked = resolve_skills(
        specialist="jr_counsel",
        message="I need judicial review grounds and Form 66 for an RTB decision",
        limit=4,
    )
    names = [p.name for p in picked]
    assert "bc-judicial-review-guide" in names
    assert "supreme-court-civil-counsel" in names

    cat = catalog_summary()
    assert cat["count"] >= 5
    assert cat["locked_guards"]


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("ALA_SQLITE_PATH", str(tmp_path / "skills_chat.sqlite3"))
    monkeypatch.delenv("ALA_POSTGRES_URL", raising=False)
    monkeypatch.delenv("APP_MODE", raising=False)

    import backend.db.connection as conn_mod
    import backend.identity.service as id_mod
    import backend.audit.ledger as aud_mod
    import backend.platform.matters as mat_mod
    import backend.platform.conversation as chat_mod
    from backend.skills_runtime import clear_skill_cache

    conn_mod._initialized = False
    id_mod._svc = None
    aud_mod._ledger = None
    mat_mod._store = None
    chat_mod._svc = None
    clear_skill_cache()

    from backend.api.main import app

    with TestClient(app) as c:
        yield c


def _auth(client: TestClient) -> dict[str, str]:
    r = client.post(
        "/v1/platform/auth/register",
        json={
            "org_name": "Skills Firm",
            "email": "skills@synthetic.invalid",
            "password": "securepass99",
        },
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_skills_endpoint(client: TestClient):
    h = _auth(client)
    r = client.get("/v1/platform/skills", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 5
    names = {s["name"] for s in body["skills"]}
    assert "bc-judicial-review-guide" in names


def test_chat_loads_skills_on_jr(client: TestClient):
    h = _auth(client)
    c = client.post(
        "/v1/platform/conversations",
        headers=h,
        json={
            "title": "JR skills",
            "chat_type": "research",
            "specialist": "jr_counsel",
            "model_mode": "balanced",
        },
    )
    assert c.status_code == 200, c.text
    cid = c.json()["conversation_id"]

    m = client.post(
        f"/v1/platform/conversations/{cid}/messages",
        headers=h,
        json={
            "content": (
                "Review this RTB decision and identify every ground for judicial review. "
                "I need a Form 66 petition strategy."
            )
        },
    )
    assert m.status_code == 200, m.text
    asst = m.json()["assistant"]
    content = asst["content"]
    meta = asst["meta"]
    assert "Form 66" in content
    assert "s.58" in content or "patent" in content.lower()
    assert meta.get("controls", {}).get("skills_loaded")
    assert "bc-judicial-review-guide" in meta["controls"]["skills_loaded"]
    assert any("Not legal advice" in w for w in meta["warnings"])
    tools = " ".join(meta.get("tool_activity") or [])
    assert "skills:" in tools


def test_chat_jr_clock_with_date(client: TestClient):
    h = _auth(client)
    c = client.post(
        "/v1/platform/conversations",
        headers=h,
        json={"specialist": "deadline_clerk", "chat_type": "research"},
    )
    cid = c.json()["conversation_id"]
    m = client.post(
        f"/v1/platform/conversations/{cid}/messages",
        headers=h,
        json={"content": "What is the JR clock if issuance was 2026-06-15 under ATA s.57?"},
    )
    assert m.status_code == 200, m.text
    content = m.json()["assistant"]["content"]
    assert "2026-08-14" in content or "JR clock" in content
    assert "Form 66" in content
