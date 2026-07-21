"""Phase 1 privilege layer — state machine, tagger, access, production gate."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.privilege_schemas import (
    MatterAccessGrant,
    PartyCommRole,
    PrincipalRole,
    PrivilegeBasis,
    PrivilegeMetadata,
    PrivilegeStatus,
    WaiverEvent,
)
from backend.privilege.access_control import (
    AuthorizationContext,
    DocumentView,
    PrivilegeAccessDenied,
    assert_document_readable,
    filter_documents_for_principal,
    storage_key_prefix,
)
from backend.privilege.production_gate import ExportItem, run_production_gate
from backend.privilege.state_machine import InvalidPrivilegeTransition, transition_privilege
from backend.privilege.tagger import propose_privilege_tag


def test_privilege_owner_is_client_not_firm():
    meta = PrivilegeMetadata(privilege_owner="client-001")
    assert meta.privilege_owner == "client-001"
    assert meta.privilege_status == PrivilegeStatus.UNCLAIMED


def test_state_machine_claim_assert_waive():
    meta = PrivilegeMetadata(privilege_owner="client-001")
    meta = transition_privilege(
        meta, PrivilegeStatus.CLAIMED, actor_id="lawyer-1", reason="advice email"
    )
    assert meta.claim_date is not None
    meta = transition_privilege(
        meta,
        PrivilegeStatus.ASSERTED,
        actor_id="lawyer-1",
        reason="list of docs",
        proceeding_id="SC-123",
    )
    assert meta.asserted_in == "SC-123"
    meta = transition_privilege(
        meta,
        PrivilegeStatus.WAIVED,
        actor_id="client-001",
        reason="limited waiver",
        waiver=WaiverEvent(
            actor_id="client-001",
            basis="limited production",
            scope="doc-set-A",
        ),
    )
    assert meta.privilege_status == PrivilegeStatus.WAIVED
    assert len(meta.waiver_events) == 1


def test_invalid_transition_blocked():
    meta = PrivilegeMetadata(privilege_owner="c1", privilege_status=PrivilegeStatus.WAIVED)
    try:
        transition_privilege(meta, PrivilegeStatus.CLAIMED, actor_id="x", reason="nope")
        raised = False
    except InvalidPrivilegeTransition:
        raised = True
    assert raised


def test_tagger_client_lawyer_advice():
    p = propose_privilege_tag(
        sender_role=PartyCommRole.CLIENT,
        recipient_role=PartyCommRole.LAWYER,
        advice_sought=True,
        advice_given=False,
        litigation_context=False,
        confidence=0.9,
    )
    assert p.proposed_basis == PrivilegeBasis.SOLICITOR_CLIENT
    assert p.finalized is False
    assert p.requires_human_review is True  # privileged tags always confirm


def test_tagger_third_party_forces_review():
    p = propose_privilege_tag(
        sender_role=PartyCommRole.CLIENT,
        recipient_role=PartyCommRole.THIRD_PARTY,
        advice_sought=True,
        advice_given=True,
        litigation_context=True,
        confidence=0.99,
    )
    assert p.proposed_basis == PrivilegeBasis.NONE
    assert p.requires_human_review is True
    assert p.confidence <= 0.7


def test_opposing_counsel_zero_access():
    doc = DocumentView(
        document_id="d1",
        matter_id="m1",
        privilege=PrivilegeMetadata(privilege_owner="c1"),
    )
    ctx = AuthorizationContext(
        user_id="opp-1",
        role=PrincipalRole.OPPOSING_COUNSEL,
        grants=[
            MatterAccessGrant(
                user_id="opp-1",
                matter_id="m1",
                role=PrincipalRole.OPPOSING_COUNSEL,
            )
        ],
    )
    assert filter_documents_for_principal([doc], ctx) == []


def test_ai_associate_task_scoped_only():
    claimed = PrivilegeMetadata(
        privilege_owner="c1",
        privilege_status=PrivilegeStatus.CLAIMED,
        privilege_basis=PrivilegeBasis.SOLICITOR_CLIENT,
        human_confirmed=True,
    )
    doc = DocumentView(document_id="d1", matter_id="m1", privilege=claimed)
    ctx_ok = AuthorizationContext(
        user_id="ai-1",
        role=PrincipalRole.AI_ASSOCIATE,
        active_task_id="task-9",
        grants=[
            MatterAccessGrant(
                user_id="ai-1",
                matter_id="m1",
                role=PrincipalRole.AI_ASSOCIATE,
                task_id="task-9",
            )
        ],
    )
    assert len(filter_documents_for_principal([doc], ctx_ok)) == 1

    ctx_wrong_task = AuthorizationContext(
        user_id="ai-1",
        role=PrincipalRole.AI_ASSOCIATE,
        active_task_id="task-OTHER",
        grants=ctx_ok.grants,
    )
    assert filter_documents_for_principal([doc], ctx_wrong_task) == []


def test_production_gate_blocks_claimed():
    item = ExportItem(
        document_id="d-priv",
        privilege=PrivilegeMetadata(
            privilege_owner="c1",
            privilege_status=PrivilegeStatus.CLAIMED,
            privilege_basis=PrivilegeBasis.SOLICITOR_CLIENT,
            human_confirmed=True,
        ),
    )
    d = run_production_gate([item], destination="tribunal")
    assert d.allowed is False
    assert d.review_queue is True
    assert d.requires_lawyer_signoff is True
    assert "d-priv" in d.blocked_document_ids


def test_production_gate_waiver_path():
    item = ExportItem(
        document_id="d-priv",
        privilege=PrivilegeMetadata(
            privilege_owner="c1",
            privilege_status=PrivilegeStatus.CLAIMED,
            human_confirmed=True,
        ),
    )
    d = run_production_gate(
        [item],
        intended_waiver=True,
        client_waiver_signed=True,
        instructing_lawyer_signed=True,
        destination="opposing",
    )
    assert d.allowed is True


def test_storage_prefix_segregation():
    p = storage_key_prefix("firm-A", "matter-B", privileged=True)
    assert p == "tenant/firm-A/matter/matter-B/privileged"
    n = storage_key_prefix("firm-A", "matter-B", privileged=False)
    assert n == "tenant/firm-A/matter/matter-B/non_privileged"


if __name__ == "__main__":
    test_privilege_owner_is_client_not_firm()
    test_state_machine_claim_assert_waive()
    test_invalid_transition_blocked()
    test_tagger_client_lawyer_advice()
    test_tagger_third_party_forces_review()
    test_opposing_counsel_zero_access()
    test_ai_associate_task_scoped_only()
    test_production_gate_blocks_claimed()
    test_production_gate_waiver_path()
    test_storage_prefix_segregation()
    print("OK: 10 privilege layer tests passed")
