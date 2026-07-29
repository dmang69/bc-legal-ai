"""HttpOnly session cookies + CSRF for browser clients; bearer remains valid."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("ALA_SQLITE_PATH", str(tmp_path / "cookie.sqlite3"))
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


def test_login_sets_httponly_session_cookie(client: TestClient):
    r = client.post(
        "/v1/platform/auth/register",
        json={
            "org_name": "Cookie Firm",
            "email": "cookie@synthetic.invalid",
            "password": "securepass99",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("token")
    assert body.get("csrf_token")
    # HttpOnly session cookie present
    assert "ala_session" in r.cookies or any(
        "ala_session" in (c or "") for c in r.headers.get_list("set-cookie")
    )


def test_bearer_still_works_without_csrf(client: TestClient):
    r = client.post(
        "/v1/platform/auth/register",
        json={
            "org_name": "Bearer Firm",
            "email": "bearer@synthetic.invalid",
            "password": "securepass99",
        },
    )
    token = r.json()["token"]
    me = client.get(
        "/v1/platform/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "bearer@synthetic.invalid"


def test_cookie_auth_requires_csrf_on_post(client: TestClient):
    r = client.post(
        "/v1/platform/auth/register",
        json={
            "org_name": "CSRF Firm",
            "email": "csrf@synthetic.invalid",
            "password": "securepass99",
        },
    )
    assert r.status_code == 200
    csrf = r.json()["csrf_token"]
    # Drop Authorization; use cookies only (TestClient stores them)
    # Create matter without CSRF → 403
    denied = client.post(
        "/v1/platform/matters",
        json={"title": "No CSRF", "synthetic": True},
    )
    assert denied.status_code == 403, denied.text

    ok = client.post(
        "/v1/platform/matters",
        headers={"X-CSRF-Token": csrf},
        json={"title": "With CSRF", "synthetic": True},
    )
    assert ok.status_code == 200, ok.text
