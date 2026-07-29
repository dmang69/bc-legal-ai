"""M1 platform foundation tests — identity, isolation, audit, evidence, citations."""

from __future__ import annotations

from pathlib import Path

import pytest

# Isolate DB per test session file
_TEST_DB = Path(__file__).resolve().parent / "_tmp_platform.sqlite3"


@pytest.fixture(autouse=True)
def _fresh_db(monkeypatch, tmp_path):
    db = tmp_path / "test.sqlite3"
    monkeypatch.setenv("ALA_SQLITE_PATH", str(db))
    monkeypatch.delenv("ALA_POSTGRES_URL", raising=False)
    # reset singletons / init flag
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
    from backend.db import init_db

    init_db(force=True)
    yield


def test_register_login_and_matter_isolation():
    from backend.identity import get_identity_service
    from backend.platform.matters import get_matter_store

    idsvc = get_identity_service()
    org = idsvc.create_organization("Test Firm")
    u1 = idsvc.register_user(
        org_id=org, email="lawyer@synthetic.invalid", password="securepass99", role="lawyer"
    )
    u2 = idsvc.register_user(
        org_id=org, email="other@synthetic.invalid", password="securepass99", role="member"
    )
    sess = idsvc.login(email="lawyer@synthetic.invalid", password="securepass99")
    assert sess.user.user_id == u1.user_id

    store = get_matter_store()
    m = store.create_matter(user=u1, title="Synthetic JR", synthetic=True)
    mid = m["matter_id"]

    # u2 has no grant
    from backend.identity import AuthError

    with pytest.raises(AuthError):
        store.get_matter(u2, mid)

    idsvc.grant_matter_access(matter_id=mid, user_id=u2.user_id, access_level="read")
    got = store.get_matter(u2, mid)
    assert got["matter_id"] == mid


def test_cross_org_isolation():
    from backend.identity import AuthError, get_identity_service
    from backend.platform.matters import get_matter_store

    idsvc = get_identity_service()
    o1 = idsvc.create_organization("Firm A")
    o2 = idsvc.create_organization("Firm B")
    a = idsvc.register_user(org_id=o1, email="a@synthetic.invalid", password="securepass99")
    b = idsvc.register_user(org_id=o2, email="b@synthetic.invalid", password="securepass99")
    store = get_matter_store()
    m = store.create_matter(user=a, title="A only", synthetic=True)
    with pytest.raises(AuthError):
        store.get_matter(b, m["matter_id"])


def test_audit_hash_chain():
    from backend.audit import get_audit_ledger

    led = get_audit_ledger()
    e1 = led.append(actor_id="u1", action="test.one", org_id="o1")
    e2 = led.append(actor_id="u1", action="test.two", org_id="o1")
    assert e2.prev_hash == e1.entry_hash
    assert led.verify_chain()["ok"] is True


def test_evidence_quarantine_and_proposition():
    from backend.identity import get_identity_service
    from backend.platform.evidence import get_evidence_service
    from backend.platform.matters import get_matter_store

    idsvc = get_identity_service()
    org = idsvc.create_organization("Ev Firm")
    u = idsvc.register_user(org_id=org, email="ev@synthetic.invalid", password="securepass99")
    m = get_matter_store().create_matter(user=u, title="Ev matter", synthetic=True)
    mid = m["matter_id"]
    ev = get_evidence_service()
    doc = ev.quarantine_upload(
        user=u,
        matter_id=mid,
        filename="note.txt",
        data=b"Hearing on 2026-01-15.",
        content_type="text/plain",
        synthetic=True,
    )
    assert doc["quarantine_status"] == "CLEAN"
    assert doc["sha256"]
    blocked = ev.quarantine_upload(
        user=u,
        matter_id=mid,
        filename="bad.exe",
        data=b"MZ",
        synthetic=True,
    )
    assert blocked["quarantine_status"] == "BLOCKED"


def test_citation_rejects_s56_retaliation():
    from backend.platform.citations import verify_citation

    r = verify_citation("RTA s.56 retaliation", expected_topic="retaliatory_eviction")
    assert r["status"] == "REJECTED"
    assert r["court_ready"] is False


def test_conflict_check_flags_party():
    from backend.identity import get_identity_service
    from backend.platform.conflicts import get_conflict_service

    idsvc = get_identity_service()
    org = idsvc.create_organization("Conf Firm")
    u = idsvc.register_user(org_id=org, email="c@synthetic.invalid", password="securepass99")
    cs = get_conflict_service()
    cs.add_party(user=u, display_name="Alex Example")
    r = cs.check_name(user=u, query_name="Alex Example")
    assert r["status"] == "PENDING_REVIEW"
    assert r["review_required"] is True
