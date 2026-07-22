"""HTTP-level platform API tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("ALA_SQLITE_PATH", str(tmp_path / "api.sqlite3"))
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


def test_platform_register_and_matter_flow(client: TestClient):
    r = client.post(
        "/v1/platform/auth/register",
        json={
            "org_name": "API Firm",
            "email": "api@synthetic.invalid",
            "password": "securepass99",
            "display_name": "API User",
        },
    )
    assert r.status_code == 200, r.text
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    m = client.post(
        "/v1/platform/matters",
        headers=headers,
        json={"title": "Demo matter", "synthetic": True},
    )
    assert m.status_code == 200
    mid = m.json()["matter_id"]

    docs = client.post(
        f"/v1/platform/matters/{mid}/documents/text",
        headers=headers,
        json={
            "filename": "memo.txt",
            "text_content": "Synthetic hearing notes.",
            "synthetic": True,
        },
    )
    assert docs.status_code == 200
    doc_id = docs.json()["document_id"]
    assert docs.json()["quarantine_status"] == "CLEAN"

    cite = client.post(
        "/v1/platform/citations/verify",
        json={"citation_text": "RTA s.56 retaliation", "expected_topic": "retaliatory_eviction"},
    )
    assert cite.status_code == 200
    rejected_citation_id = cite.json()["verification_id"]
    assert cite.json()["status"] == "REJECTED"

    good_cite = client.post(
        "/v1/platform/citations/verify",
        json={"citation_text": "RTA s.32", "matter_id": mid, "expected_topic": "repair"},
    )
    assert good_cite.status_code == 200
    provisional_citation_id = good_cite.json()["verification_id"]
    assert good_cite.json()["status"] == "PROVISIONAL"

    audit = client.get("/v1/platform/audit/verify", headers=headers)
    assert audit.status_code == 200
    assert audit.json()["ok"] is True

    health = client.get("/health")
    assert health.json()["status"] == "ok"
    assert health.json().get("db_backend") == "sqlite"

    cons = client.post(
        f"/v1/platform/matters/{mid}/consents",
        headers=headers,
        json={
            "subject_id": "client-1",
            "category": "AI_ANALYSIS",
            "purpose": "organize synthetic evidence",
        },
    )
    assert cons.status_code == 200
    assert cons.json()["status"] == "GRANTED"

    d66 = client.get(f"/v1/platform/matters/{mid}/drafts/form-66", headers=headers)
    assert d66.status_code == 200
    assert d66.json()["court_ready"] is False
    assert d66.json().get("form_number") == "66"

    workspace = client.post(
        "/v1/platform/workspace/analyze",
        json={
            "message": "Summarize this synthetic RTB record and check RTA s.56 retaliation.",
            "mode": "research",
            "matter_id": mid,
        },
    )
    assert workspace.status_code == 200
    body = workspace.json()
    assert body["safety"]["court_ready"] is False
    assert body["safety"]["legal_advice"] is False
    assert body["classification"]["requires_human_review"] is True
    assert body["citations"]
    assert any(c["status"] == "REJECTED" for c in body["citations"])

    citation_audit = client.get(f"/v1/platform/citations/audit?matter_id={mid}")
    assert citation_audit.status_code == 200
    audited = citation_audit.json()["citations"]
    assert audited
    assert any(item["source_id"] == "source_bc_laws" for item in audited)
    assert all(item["court_ready"] is False for item in audited)
    assert all("source_hash" in item for item in audited)

    blocked_manifest = client.post(
        f"/v1/platform/matters/{mid}/exports/manifest",
        headers=headers,
        json={"document_ids": [doc_id], "citation_ids": [rejected_citation_id]},
    )
    assert blocked_manifest.status_code == 200
    assert blocked_manifest.json()["status"] == "BLOCKED"
    assert blocked_manifest.json()["court_ready"] is False
    assert blocked_manifest.json()["blockers"]

    approved_manifest = client.post(
        f"/v1/platform/matters/{mid}/exports/manifest",
        headers=headers,
        json={
            "document_ids": [doc_id],
            "citation_ids": [provisional_citation_id],
            "human_confirmed_facts": True,
            "citation_reviewed": True,
            "privilege_reviewed": True,
            "lawyer_approved": True,
        },
    )
    assert approved_manifest.status_code == 200
    assert approved_manifest.json()["status"] == "APPROVED"
    assert approved_manifest.json()["court_ready"] is True

    manifests = client.get(f"/v1/platform/matters/{mid}/exports/manifest", headers=headers)
    assert manifests.status_code == 200
    assert len(manifests.json()["manifests"]) >= 2

    conv = client.post(
        "/v1/platform/workspace/conversations",
        headers=headers,
        json={"matter_id": mid, "title": "JR research", "mode": "research"},
    )
    assert conv.status_code == 200, conv.text
    cid = conv.json()["conversation_id"]
    msg = client.post(
        f"/v1/platform/workspace/conversations/{cid}/messages",
        headers=headers,
        json={"author": "user", "body": "Check RTA s.32 repair issue", "metadata": {"mode": "research"}},
    )
    assert msg.status_code == 200
    assert msg.json()["metadata"]["mode"] == "research"

    loaded = client.get(f"/v1/platform/workspace/conversations/{cid}", headers=headers)
    assert loaded.status_code == 200
    assert loaded.json()["messages"][0]["body"] == "Check RTA s.32 repair issue"

    convs = client.get(f"/v1/platform/workspace/conversations?matter_id={mid}", headers=headers)
    assert convs.status_code == 200
    assert any(item["conversation_id"] == cid for item in convs.json()["conversations"])


def test_workspace_analyze_blocks_identifiers_in_public_demo(client: TestClient, monkeypatch):
    monkeypatch.setenv("APP_MODE", "public_demo")
    blocked = client.post(
        "/v1/platform/workspace/analyze",
        json={
            "message": "Please analyze RTB-123456 and phone 604-555-1212.",
            "mode": "matter",
        },
    )
    assert blocked.status_code == 403
    assert "Public demo accepts fictional scenarios only" in blocked.text

    persist = client.post(
        "/v1/platform/workspace/conversations",
        headers={"Authorization": "Bearer invalid"},
        json={"title": "Should not persist", "mode": "general"},
    )
    assert persist.status_code in {401, 403}
