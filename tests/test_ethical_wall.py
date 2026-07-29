"""Deny-first ethical wall: blocks owner/admin when access_level=ethical_wall."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _fresh_db(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ALA_SQLITE_PATH", str(tmp_path / "ethical.sqlite3"))
    monkeypatch.delenv("ALA_POSTGRES_URL", raising=False)

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


def test_ethical_wall_blocks_owner():
    from backend.identity import get_identity_service
    from backend.platform.matters import get_matter_store

    idsvc = get_identity_service()
    org = idsvc.create_organization("Wall Firm")
    owner = idsvc.register_user(
        org_id=org,
        email="owner@synthetic.invalid",
        password="securepass99",
        role="owner",
    )
    store = get_matter_store()
    m = store.create_matter(user=owner, title="Walled matter", synthetic=True)
    mid = m["matter_id"]

    # Owner can access before wall
    assert idsvc.can_access_matter(owner, mid) is True

    idsvc.grant_matter_access(
        matter_id=mid,
        user_id=owner.user_id,
        access_level="ethical_wall",
        granted_by="system",
    )
    assert idsvc.can_access_matter(owner, mid) is False
    assert idsvc.can_access_matter(owner, mid, min_level="admin") is False


def test_ethical_wall_blocks_admin_and_member():
    from backend.identity import get_identity_service
    from backend.platform.matters import get_matter_store

    idsvc = get_identity_service()
    org = idsvc.create_organization("Wall Firm 2")
    owner = idsvc.register_user(
        org_id=org,
        email="o2@synthetic.invalid",
        password="securepass99",
        role="owner",
    )
    admin = idsvc.register_user(
        org_id=org,
        email="admin@synthetic.invalid",
        password="securepass99",
        role="admin",
    )
    member = idsvc.register_user(
        org_id=org,
        email="member@synthetic.invalid",
        password="securepass99",
        role="member",
    )
    store = get_matter_store()
    m = store.create_matter(user=owner, title="Shared", synthetic=True)
    mid = m["matter_id"]

    idsvc.grant_matter_access(matter_id=mid, user_id=admin.user_id, access_level="admin")
    idsvc.grant_matter_access(matter_id=mid, user_id=member.user_id, access_level="write")
    assert idsvc.can_access_matter(admin, mid) is True
    assert idsvc.can_access_matter(member, mid) is True

    idsvc.grant_matter_access(matter_id=mid, user_id=admin.user_id, access_level="ethical_wall")
    idsvc.grant_matter_access(matter_id=mid, user_id=member.user_id, access_level="ethical_wall")
    assert idsvc.can_access_matter(admin, mid) is False
    assert idsvc.can_access_matter(member, mid) is False


def test_no_membership_member_denied_owner_allowed():
    from backend.identity import get_identity_service
    from backend.platform.matters import get_matter_store

    idsvc = get_identity_service()
    org = idsvc.create_organization("Wall Firm 3")
    owner = idsvc.register_user(
        org_id=org,
        email="o3@synthetic.invalid",
        password="securepass99",
        role="owner",
    )
    stranger = idsvc.register_user(
        org_id=org,
        email="stranger@synthetic.invalid",
        password="securepass99",
        role="member",
    )
    store = get_matter_store()
    m = store.create_matter(user=owner, title="Private", synthetic=True)
    mid = m["matter_id"]
    assert idsvc.can_access_matter(owner, mid) is True
    assert idsvc.can_access_matter(stranger, mid) is False
