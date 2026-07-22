"""Phase 3–4 / 4-4 FastAPI surface (in-memory)."""

from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from backend.api.main import app  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["phase"] == "3-4+4-4"


def test_design_locks(client):
    r = client.get("/v1/design-locks")
    assert r.json()["petition_form"] == "Form 66"
    assert r.json()["consent_is_not_privilege"] is True


def test_consent_grant_evaluate_withdraw(client):
    m = "MAT-API-1"
    r = client.post(
        f"/v1/matters/{m}/consents",
        json={
            "subject_id": "client-1",
            "category": "AI_ANALYSIS",
            "purpose": "organize evidence",
        },
    )
    assert r.status_code == 200
    cid = r.json()["consent_id"]

    client.post(
        f"/v1/matters/{m}/consents",
        json={
            "subject_id": "client-1",
            "category": "PHOTOGRAPHS",
            "purpose": "unit photos",
        },
    )
    ev = client.post(
        "/v1/consents/evaluate-operation",
        json={
            "matter_id": m,
            "subject_id": "client-1",
            "data_categories": ["PHOTOGRAPHS"],
            "purpose": "extract dates",
            "model_destination": "PRIVATE_INFERENCE_ONLY",
        },
    )
    assert ev.status_code == 200
    assert ev.json()["permitted"] is True

    w = client.post(f"/v1/consents/{cid}/withdraw")
    assert w.status_code == 200


def test_exception_critical_freeze(client):
    m = "MAT-API-2"
    r = client.post(
        f"/v1/matters/{m}/exceptions",
        json={
            "category": "HALLUCINATED_AUTHORITY_ATTEMPT",
            "message": "Invented section",
            "affected_artifacts": ["draft_1"],
        },
    )
    assert r.status_code == 200
    assert r.json()["freeze_export"] is True
    lst = client.get(f"/v1/matters/{m}/exceptions")
    assert lst.json()["export_frozen"] is True


def test_jr_clock(client):
    r = client.post(
        "/v1/deadlines/jr-clock",
        json={
            "matter_id": "M1",
            "issuance_date": "2026-01-15",
            "human_confirmed": True,
        },
    )
    assert r.status_code == 200
    assert r.json()["primary_deadline"] == "2026-03-16"
    assert r.json()["clock_mode"] == "STANDARD_60_FROM_ISSUANCE"


def test_post_resolution_ingest(client):
    text = (
        "Decision dated 2026-01-15. The landlord shall pay the tenant $500 within 15 days. "
        "The landlord must repair the bathroom within 30 days."
    )
    r = client.post(
        "/v1/matters/MAT-PR/post-resolution/ingest",
        json={
            "text": text,
            "decision_date": "2026-01-15",
            "predicted_classes": ["MONETARY_AWARD"],
            "client_role": "tenant",
            "open_jr_if_unfavorable": True,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["outcome"]["clocks"]
    assert "jr" in body
    assert body["jr"]["petition"]["form_code"] == "Form 66"

    g = client.get("/v1/matters/MAT-PR/post-resolution")
    assert g.status_code == 200
    assert g.json()["outcome"] is not None


def test_enforcement_package(client):
    r = client.post(
        "/v1/matters/MAT-PR/post-resolution/enforcement",
        json={"package_type": "RTB_ENFORCEMENT", "order_summary": "repair order"},
    )
    assert r.status_code == 200
    assert r.json()["documents"]
