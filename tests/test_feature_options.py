"""Structured feature options catalog."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("ALA_SQLITE_PATH", str(tmp_path / "feat.sqlite3"))
    monkeypatch.delenv("ALA_POSTGRES_URL", raising=False)
    monkeypatch.setenv("ALA_RATE_LIMIT_DISABLED", "1")
    monkeypatch.delenv("ALA_ALLOW_EXTERNAL_LLM", raising=False)
    monkeypatch.delenv("ALA_WEB_RESEARCH", raising=False)

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
            "org_name": "Features Firm",
            "email": "features@synthetic.invalid",
            "password": "securepass99",
        },
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_features_manifest(client: TestClient):
    h = _auth(client)
    r = client.get("/v1/platform/features", headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["court_ready_default"] is False
    assert body["legal_advice"] is False
    assert body["categories"]
    assert len(body["features"]) >= 15
    ids = {f["id"] for f in body["features"]}
    assert "ai.puter_base" in ids
    assert "ai.openclaw" in ids
    assert "ai.arena" in ids
    assert "ai.kimi" in ids
    assert "client.windows_setup" in ids
    assert "client.chrome_pwa" in ids
    assert "gov.court_ready_fail_closed" in ids
    # always-on failsafe
    safe = next(f for f in body["features"] if f["id"] == "ai.safe_local")
    assert safe["enabled"] is True
    ext = next(f for f in body["features"] if f["id"] == "ai.external_cloud_llm")
    assert ext["enabled"] is False
    assert "pilot_synthetic" in body["selection_guide"]


def test_features_category_filter(client: TestClient):
    h = _auth(client)
    r = client.get("/v1/platform/features?category=ai", headers=h)
    assert r.status_code == 200
    for f in r.json()["features"]:
        assert f["category"] == "ai"


def test_suite_embeds_feature_options(client: TestClient):
    h = _auth(client)
    r = client.get("/v1/platform/ai/suite", headers=h)
    assert r.status_code == 200
    fo = r.json().get("feature_options") or {}
    assert fo.get("features")
    assert r.json()["endpoints"].get("features") == "/v1/platform/features"


def test_catalog_module_unit():
    from backend.platform.feature_options import FEATURE_CATALOG, features_manifest

    cats = {f.category for f in FEATURE_CATALOG}
    assert cats >= {"install", "ai", "legal", "productivity", "governance"}
    m = features_manifest()
    assert m["by_category"]["ai"]
