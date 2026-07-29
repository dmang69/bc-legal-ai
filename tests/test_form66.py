"""Form 66 petition scaffold DOCX — structure and fail-closed court_ready."""

from __future__ import annotations

import io
import zipfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("ALA_SQLITE_PATH", str(tmp_path / "f66.sqlite3"))
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


def test_build_form66_has_required_parts():
    from backend.identity import UserInfo
    from backend.platform.form66 import build_form66_docx

    user = UserInfo(
        user_id="u1",
        org_id="o1",
        email="lawyer@synthetic.invalid",
        display_name="L",
        role="lawyer",
        status="ACTIVE",
    )
    outline = {
        "status": "ok",
        "title": "PETITION OUTLINE",
        "statute_route": "JRPA",
        "grounds": [
            {
                "ground_id": "1",
                "title": "Patent Unreasonableness",
                "standard": "Patent Unreasonableness",
                "sub_grounds": [
                    {
                        "sub_id": "1a",
                        "description": "Failed to engage with key evidence",
                        "cites": [
                            {
                                "kind": "authority",
                                "label": "RTA s.47",
                                "citation_short": "RTA s. 47 (VERIFY on BC Laws)",
                                "verification_status": "UNVERIFIED",
                            }
                        ],
                    }
                ],
            }
        ],
    }
    result = build_form66_docx(
        matter_id="mat_demo",
        user=user,
        outline=outline,
        matter_title="Demo JR",
    )
    assert result.ok
    assert result.court_ready is False
    assert result.form_number == "66"
    assert "orders_sought" in result.sections
    assert "legal_basis" in result.sections
    # DOCX magic
    assert result.docx_bytes[:2] == b"PK"
    # Readable XML contains Form 66 and ground text
    with zipfile.ZipFile(io.BytesIO(result.docx_bytes)) as zf:
        xml = zf.read("word/document.xml").decode("utf-8", errors="replace")
    assert "Form 66" in xml
    assert "Patent Unreasonableness" in xml
    assert "Part 1" in xml or "ORDERS SOUGHT" in xml


def test_form66_docx_route(client: TestClient):
    r = client.post(
        "/v1/platform/auth/register",
        json={
            "org_name": "F66 Firm",
            "email": "f66@synthetic.invalid",
            "password": "securepass99",
        },
    )
    headers = {"Authorization": f"Bearer {r.json()['token']}"}
    m = client.post(
        "/v1/platform/matters",
        headers=headers,
        json={"title": "JR matter", "synthetic": True, "client_label": "Tenant X"},
    )
    mid = m.json()["matter_id"]
    docx = client.get(f"/v1/platform/matters/{mid}/drafts/form-66.docx", headers=headers)
    assert docx.status_code == 200
    assert docx.content[:2] == b"PK"
    assert docx.headers.get("X-Form-Number") == "66"
    assert docx.headers.get("X-Court-Ready") == "false"


def test_court_package_includes_form66(client: TestClient, tmp_path, monkeypatch):
    """Approved manifest package embeds Form 66 scaffold under forms/."""
    from backend.db import get_connection, init_db
    from backend.identity import get_identity_service
    from backend.platform.court_export import build_court_package
    import backend.db.connection as conn_mod
    import backend.identity.service as id_mod

    monkeypatch.setenv("ALA_SQLITE_PATH", str(tmp_path / "pkg66.sqlite3"))
    monkeypatch.delenv("ALA_POSTGRES_URL", raising=False)
    conn_mod._initialized = False
    id_mod._svc = None
    init_db(force=True)
    idsvc = get_identity_service()
    org = idsvc.create_organization("Pkg66")
    user = idsvc.register_user(
        org_id=org, email="pkg66@synthetic.invalid", password="securepass99", role="owner"
    )
    mid = "mat_f66pkg"
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO matters (matter_id, title, org_id, synthetic, client_label) "
            "VALUES (?, ?, ?, 1, ?)",
            (mid, "JR", org, "Tenant"),
        )
        conn.execute(
            """
            INSERT INTO export_manifests
            (manifest_id, matter_id, destination, document_ids_json, citation_ids_json,
             status, court_ready, privilege_decision_json, blockers_json, approvals_json, created_by)
            VALUES (?, ?, 'export', '[]', '[]', 'APPROVED', 1, '{}', '[]', '{}', ?)
            """,
            ("exp_f66", mid, user.user_id),
        )
    idsvc.grant_matter_access(matter_id=mid, user_id=user.user_id, access_level="admin")
    result = build_court_package(user=user, matter_id=mid, manifest_id="exp_f66")
    assert result.ok
    with zipfile.ZipFile(io.BytesIO(result.package_bytes)) as zf:
        names = zf.namelist()
    assert any(n.startswith("forms/") and n.endswith(".docx") for n in names)
    assert "forms/form66_meta.json" in names
