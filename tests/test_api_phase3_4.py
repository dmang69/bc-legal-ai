"""Phase 3–4 / 4-4 FastAPI surface (authenticated)."""

from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Isolated SQLite + reset singletons so auth/matters are reproducible."""
    monkeypatch.setenv("ALA_SQLITE_PATH", str(tmp_path / "phase34.sqlite3"))
    monkeypatch.delenv("ALA_POSTGRES_URL", raising=False)
    monkeypatch.delenv("APP_MODE", raising=False)

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


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    r = client.post(
        "/v1/platform/auth/register",
        json={
            "org_name": "Phase34 Firm",
            "email": "phase34@synthetic.invalid",
            "password": "securepass99",
            "display_name": "Phase34 User",
        },
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture
def matter_id(client: TestClient, auth_headers: dict[str, str]) -> str:
    m = client.post(
        "/v1/platform/matters",
        headers=auth_headers,
        json={"title": "Phase34 synthetic matter", "synthetic": True},
    )
    assert m.status_code == 200, m.text
    return m.json()["matter_id"]


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["phase"] == "m1-platform"


def test_design_locks(client: TestClient):
    r = client.get("/v1/design-locks")
    assert r.json()["petition_form"] == "Form 66"
    assert r.json()["consent_is_not_privilege"] is True


def test_unauthenticated_legacy_routes_denied(client: TestClient):
    """Legacy HITL routes must not accept anonymous callers after auth hardening."""
    r = client.post(
        "/v1/matters/MAT-NOAUTH/consents",
        json={
            "subject_id": "client-1",
            "category": "AI_ANALYSIS",
            "purpose": "should fail",
        },
    )
    assert r.status_code == 401


def test_consent_grant_evaluate_withdraw(
    client: TestClient, auth_headers: dict[str, str], matter_id: str
):
    r = client.post(
        f"/v1/matters/{matter_id}/consents",
        headers=auth_headers,
        json={
            "subject_id": "client-1",
            "category": "AI_ANALYSIS",
            "purpose": "organize evidence",
        },
    )
    assert r.status_code == 200, r.text
    cid = r.json()["consent_id"]

    client.post(
        f"/v1/matters/{matter_id}/consents",
        headers=auth_headers,
        json={
            "subject_id": "client-1",
            "category": "PHOTOGRAPHS",
            "purpose": "unit photos",
        },
    )
    ev = client.post(
        "/v1/consents/evaluate-operation",
        headers=auth_headers,
        json={
            "matter_id": matter_id,
            "subject_id": "client-1",
            "data_categories": ["PHOTOGRAPHS"],
            "purpose": "extract dates",
            "model_destination": "PRIVATE_INFERENCE_ONLY",
        },
    )
    assert ev.status_code == 200, ev.text
    assert ev.json()["permitted"] is True

    w = client.post(f"/v1/consents/{cid}/withdraw", headers=auth_headers)
    assert w.status_code == 200, w.text


def test_exception_critical_freeze(
    client: TestClient, auth_headers: dict[str, str], matter_id: str
):
    r = client.post(
        f"/v1/matters/{matter_id}/exceptions",
        headers=auth_headers,
        json={
            "category": "HALLUCINATED_AUTHORITY_ATTEMPT",
            "message": "Invented section",
            "affected_artifacts": ["draft_1"],
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["freeze_export"] is True
    lst = client.get(f"/v1/matters/{matter_id}/exceptions", headers=auth_headers)
    assert lst.status_code == 200, lst.text
    assert lst.json()["export_frozen"] is True


def test_jr_clock(client: TestClient, auth_headers: dict[str, str], matter_id: str):
    r = client.post(
        "/v1/deadlines/jr-clock",
        headers=auth_headers,
        json={
            "matter_id": matter_id,
            "issuance_date": "2026-01-15",
            "finality_known": True,
            "enabling_act_known": True,
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["primary_deadline"] == "2026-03-16"
    assert body["clock_mode"] == "STANDARD_60_FROM_ISSUANCE"


def test_post_resolution_ingest(
    client: TestClient, auth_headers: dict[str, str], matter_id: str
):
    text = (
        "Decision dated 2026-01-15. The landlord shall pay the tenant $500 within 15 days. "
        "The landlord must repair the bathroom within 30 days."
    )
    r = client.post(
        f"/v1/matters/{matter_id}/post-resolution/ingest",
        headers=auth_headers,
        json={
            "text": text,
            "decision_date": "2026-01-15",
            "predicted_classes": ["MONETARY_AWARD"],
            "client_role": "tenant",
            "open_jr_if_unfavorable": True,
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["outcome"]["clocks"]
    assert "jr" in body
    assert body["jr"]["petition"]["form_code"] == "Form 66"

    g = client.get(f"/v1/matters/{matter_id}/post-resolution", headers=auth_headers)
    assert g.status_code == 200
    assert g.json()["outcome"] is not None


def test_enforcement_package(
    client: TestClient, auth_headers: dict[str, str], matter_id: str
):
    r = client.post(
        f"/v1/matters/{matter_id}/post-resolution/enforcement",
        headers=auth_headers,
        json={"package_type": "RTB_ENFORCEMENT", "order_summary": "repair order"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["documents"]
