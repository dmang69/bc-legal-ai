"""Cross-matter / cross-org denial on legacy authenticated matter routes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("ALA_SQLITE_PATH", str(tmp_path / "xmat.sqlite3"))
    monkeypatch.delenv("ALA_POSTGRES_URL", raising=False)
    monkeypatch.delenv("APP_MODE", raising=False)
    monkeypatch.setenv("ALA_RATE_LIMIT_DISABLED", "1")

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


def _register(client: TestClient, org: str, email: str) -> dict[str, str]:
    r = client.post(
        "/v1/platform/auth/register",
        json={
            "org_name": org,
            "email": email,
            "password": "securepass99",
            "display_name": email,
        },
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_cross_org_cannot_use_other_matter_consent(client: TestClient):
    a = _register(client, "Org A", "a@synthetic.invalid")
    b = _register(client, "Org B", "b@synthetic.invalid")

    m = client.post(
        "/v1/platform/matters",
        headers=a,
        json={"title": "A matter", "synthetic": True},
    )
    assert m.status_code == 200
    mid = m.json()["matter_id"]

    denied = client.post(
        f"/v1/matters/{mid}/consents",
        headers=b,
        json={
            "subject_id": "client-x",
            "category": "AI_ANALYSIS",
            "purpose": "should fail",
        },
    )
    assert denied.status_code == 403, denied.text

    ok = client.post(
        f"/v1/matters/{mid}/consents",
        headers=a,
        json={
            "subject_id": "client-x",
            "category": "AI_ANALYSIS",
            "purpose": "owner ok",
        },
    )
    assert ok.status_code == 200, ok.text


def test_cross_org_jr_clock_denied(client: TestClient):
    a = _register(client, "Org A2", "a2@synthetic.invalid")
    b = _register(client, "Org B2", "b2@synthetic.invalid")
    m = client.post(
        "/v1/platform/matters",
        headers=a,
        json={"title": "JR matter", "synthetic": True},
    )
    mid = m.json()["matter_id"]
    denied = client.post(
        "/v1/deadlines/jr-clock",
        headers=b,
        json={"matter_id": mid, "issuance_date": "2026-01-15"},
    )
    assert denied.status_code == 403, denied.text
