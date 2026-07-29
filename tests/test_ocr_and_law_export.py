"""OCR flags, BC Laws offline fetch, court package gate."""

from __future__ import annotations

import base64
import io

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("ALA_SQLITE_PATH", str(tmp_path / "ocr.sqlite3"))
    monkeypatch.delenv("ALA_POSTGRES_URL", raising=False)
    monkeypatch.delenv("APP_MODE", raising=False)
    monkeypatch.setenv("ALA_RATE_LIMIT_DISABLED", "1")
    monkeypatch.setenv("ALA_BC_LAWS_OFFLINE", "1")
    monkeypatch.setenv("ALA_OCR_DISABLED", "1")

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


def _auth_matter(client: TestClient):
    r = client.post(
        "/v1/platform/auth/register",
        json={
            "org_name": "OCR Firm",
            "email": "ocr@synthetic.invalid",
            "password": "securepass99",
        },
    )
    assert r.status_code == 200, r.text
    headers = {"Authorization": f"Bearer {r.json()['token']}"}
    m = client.post(
        "/v1/platform/matters",
        headers=headers,
        json={"title": "OCR matter", "synthetic": True},
    )
    return headers, m.json()["matter_id"]


def test_pdf_extract_minimal_pdf(client: TestClient):
    """Minimal valid-ish PDF header path — not a PDF should fail closed."""
    headers, mid = _auth_matter(client)
    raw = b"not-a-pdf"
    b64 = base64.b64encode(raw).decode("ascii")
    r = client.post(
        f"/v1/platform/matters/{mid}/documents/pdf-extract",
        headers=headers,
        json={"filename": "x.pdf", "content_base64": b64},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False
    assert body["court_ready"] is False


def test_extract_with_ocr_marks_needs_when_disabled():
    from backend.platform.ocr import extract_with_ocr

    # Not a PDF
    r = extract_with_ocr(b"")
    assert r.ok is False


def test_bc_laws_offline(client: TestClient):
    headers, _mid = _auth_matter(client)
    r = client.post(
        "/v1/platform/knowledge/bc-laws/fetch",
        headers=headers,
        json={"source_key": "RTA", "persist": False},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False
    assert body["court_ready"] is False
    assert "OFFLINE" in body["error"] or "offline" in body["error"].lower()


def test_bc_laws_catalog(client: TestClient):
    headers, _ = _auth_matter(client)
    r = client.get("/v1/platform/knowledge/bc-laws/catalog", headers=headers)
    assert r.status_code == 200
    assert "RTA" in r.json()["statutes"]


def test_court_package_blocked_without_approved_manifest(client: TestClient):
    headers, mid = _auth_matter(client)
    r = client.post(
        f"/v1/platform/matters/{mid}/exports/fake_manifest/package",
        headers=headers,
    )
    assert r.status_code == 400


def test_currency_line_parser():
    from knowledgebase.updater.bc_laws_fetcher import extract_currency_line

    html = "<p>This Act is current to July 14, 2026</p>"
    assert extract_currency_line(html) == "July 14, 2026"


def test_build_docx_package_unit(tmp_path, monkeypatch):
    monkeypatch.setenv("ALA_SQLITE_PATH", str(tmp_path / "pkg.sqlite3"))
    monkeypatch.delenv("ALA_POSTGRES_URL", raising=False)
    import backend.db.connection as conn_mod
    import backend.identity.service as id_mod

    conn_mod._initialized = False
    id_mod._svc = None
    from backend.db import init_db
    from backend.identity import get_identity_service
    from backend.platform.court_export import build_court_package
    from backend.db import get_connection
    import json

    init_db(force=True)
    idsvc = get_identity_service()
    org = idsvc.create_organization("Pkg")
    user = idsvc.register_user(
        org_id=org, email="pkg@synthetic.invalid", password="securepass99", role="owner"
    )
    # Insert synthetic approved manifest
    mid = "mat_testpkg"
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO matters (matter_id, title, org_id, synthetic) VALUES (?, ?, ?, 1)",
            (mid, "T", org),
        )
        conn.execute(
            """
            INSERT INTO export_manifests
            (manifest_id, matter_id, destination, document_ids_json, citation_ids_json,
             status, court_ready, privilege_decision_json, blockers_json, approvals_json, created_by)
            VALUES (?, ?, 'export', '[]', '[]', 'APPROVED', 1, '{}', '[]', '{}', ?)
            """,
            ("exp_ok", mid, user.user_id),
        )
    result = build_court_package(user=user, matter_id=mid, manifest_id="exp_ok")
    assert result.ok is True
    assert result.court_ready is True
    assert result.package_bytes[:2] == b"PK"  # zip
