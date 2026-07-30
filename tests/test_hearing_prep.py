"""Tribunal hearing preparation skill + chat routing."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("ALA_SQLITE_PATH", str(tmp_path / "hearing.sqlite3"))
    monkeypatch.delenv("ALA_POSTGRES_URL", raising=False)
    monkeypatch.setenv("ALA_RATE_LIMIT_DISABLED", "1")

    import backend.db.connection as conn_mod
    import backend.identity.service as id_mod
    import backend.audit.ledger as aud_mod
    import backend.platform.matters as mat_mod
    import backend.platform.conversation as chat_mod
    import backend.platform.model_providers as mp
    import backend.skills_runtime.loader as sk

    conn_mod._initialized = False
    id_mod._svc = None
    aud_mod._ledger = None
    mat_mod._store = None
    chat_mod._svc = None
    mp.reset_model_provider_registry()
    sk.clear_skill_cache()

    from backend.api.main import app

    with TestClient(app) as c:
        yield c


def _auth(client: TestClient) -> dict[str, str]:
    r = client.post(
        "/v1/platform/auth/register",
        json={
            "org_name": "Hearing Firm",
            "email": "hearing@synthetic.invalid",
            "password": "securepass99",
        },
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_skill_files_exist():
    base = ROOT / "skills" / "tribunal-hearing-prep"
    assert (base / "SKILL.md").is_file()
    assert (base / "templates" / "binder-index.md").is_file()
    assert (base / "templates" / "hearing-outline.md").is_file()
    assert (base / "templates" / "witness-qa-sim.md").is_file()


def test_specialist_listed(client: TestClient):
    h = _auth(client)
    r = client.get("/v1/platform/workspace/specialists", headers=h)
    assert r.status_code == 200
    ids = {s["id"] for s in r.json()["specialists"]}
    assert "hearing_prep" in ids


def test_hearing_slash_chat(client: TestClient):
    h = _auth(client)
    c = client.post(
        "/v1/platform/conversations",
        headers=h,
        json={"title": "Hearing", "specialist": "hearing_prep"},
    )
    cid = c.json()["conversation_id"]
    m = client.post(
        f"/v1/platform/conversations/{cid}/messages",
        headers=h,
        json={
            "content": "/hearing prep RTB decision — dissect record, binder tabs, witness Q&A",
        },
    )
    assert m.status_code == 200, m.text
    content = m.json()["assistant"]["content"]
    assert "Dissect the record" in content or "record" in content.lower()
    assert "binder" in content.lower()
    assert "witness" in content.lower() or "Q&A" in content
    assert "Not legal advice" in content or "not legal advice" in content.lower()
    meta = m.json()["assistant"]["meta"]
    assert meta.get("work_panel", {}).get("view") == "hearing_prep"


def test_openclaw_hearing_tools(client: TestClient):
    h = _auth(client)
    r = client.post(
        "/v1/platform/ai/openclaw/run",
        headers=h,
        json={
            "goal": "Prepare RTB judicial review hearing: binder and witness simulation",
            "auto_approve": False,
            "execute": True,
        },
    )
    assert r.status_code == 200, r.text
    tools = {s["tool_id"] for s in r.json().get("steps") or []}
    assert "hearing_binder_index" in tools or "hearing_record_map" in tools


def test_feature_option_hearing_prep(client: TestClient):
    h = _auth(client)
    r = client.get("/v1/platform/features?category=legal", headers=h)
    assert r.status_code == 200
    ids = {f["id"] for f in r.json()["features"]}
    assert "legal.hearing_prep" in ids
