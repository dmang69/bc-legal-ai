"""P0 abuse controls: auth rate limits + security headers."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("ALA_SQLITE_PATH", str(tmp_path / "rl.sqlite3"))
    monkeypatch.delenv("ALA_POSTGRES_URL", raising=False)
    monkeypatch.delenv("APP_MODE", raising=False)
    # Explicitly enable limits for this suite (conftest disables elsewhere).
    monkeypatch.setenv("ALA_RATE_LIMIT_DISABLED", "0")
    monkeypatch.setenv("ALA_RATE_LIMIT_LOGIN", "3")
    monkeypatch.setenv("ALA_RATE_LIMIT_LOGIN_WINDOW", "60")
    monkeypatch.setenv("ALA_RATE_LIMIT_REGISTER", "3")
    monkeypatch.setenv("ALA_RATE_LIMIT_REGISTER_WINDOW", "60")

    import backend.db.connection as conn_mod
    import backend.identity.service as id_mod
    import backend.audit.ledger as aud_mod
    import backend.platform.matters as mat_mod
    import backend.platform.evidence as ev_mod
    import backend.api.rate_limit as rl_mod

    conn_mod._initialized = False
    id_mod._svc = None
    aud_mod._ledger = None
    mat_mod._store = None
    ev_mod._ev = None
    rl_mod.reset_rate_limiter()
    rl_mod.set_auth_rules_for_tests(
        login=rl_mod.RateLimitRule(limit=3, window_seconds=60, name="auth.login"),
        register=rl_mod.RateLimitRule(limit=3, window_seconds=60, name="auth.register"),
    )

    from backend.api.main import app

    with TestClient(app) as c:
        yield c


def test_security_headers_present(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("Referrer-Policy") == "no-referrer"
    assert "default-src" in (r.headers.get("Content-Security-Policy") or "")


def test_login_rate_limit_returns_429(client: TestClient):
    # Register once so login can attempt
    reg = client.post(
        "/v1/platform/auth/register",
        json={
            "org_name": "RL Firm",
            "email": "rl@synthetic.invalid",
            "password": "securepass99",
        },
    )
    assert reg.status_code == 200, reg.text
    from backend.api.rate_limit import reset_rate_limiter

    reset_rate_limiter()

    codes = []
    for _ in range(5):
        r = client.post(
            "/v1/platform/auth/login",
            json={"email": "rl@synthetic.invalid", "password": "wrong-password"},
        )
        codes.append(r.status_code)
    assert 429 in codes, codes
    assert codes.count(401) + codes.count(429) == 5


def test_register_rate_limit_returns_429(client: TestClient):
    from backend.api.rate_limit import reset_rate_limiter

    reset_rate_limiter()
    codes = []
    for i in range(5):
        r = client.post(
            "/v1/platform/auth/register",
            json={
                "org_name": f"RL Firm {i}",
                "email": f"rl{i}@synthetic.invalid",
                "password": "securepass99",
            },
        )
        codes.append(r.status_code)
    assert 429 in codes, codes
