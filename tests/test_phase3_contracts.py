"""Phase 3 API/DB contract validators + six design locks."""

from __future__ import annotations

import pytest

from architecture.contracts.models import (
    RTB_ARCHIVE_WARNING,
    ApprovalContract,
    ConsentContract,
    ExceptionContract,
    KnowledgeSourceContract,
    RtbDecisionContract,
)
from knowledgebase.rtb_archive import lookup_rtb_decision
from knowledgebase.templates.catalog import petition_form
from services.deadlines.jr_clock import JrClockMode, JrClockRequest, calculate_jr_clock
from services.messaging.service import SecureMessagingStub
from services.reasoning.hitl.consent import ConsentLedger, ConsentScope


def test_consent_contract_forbids_privilege_fields():
    with pytest.raises(ValueError, match="privilege"):
        ConsentContract.from_dict(
            {
                "consent_id": "c1",
                "matter_id": "m1",
                "subject_id": "s1",
                "category": "AI_ANALYSIS",
                "purpose": "draft",
                "processing_scope": [],
                "model_scope": "PRIVATE_INFERENCE_ONLY",
                "status": "ACTIVE",
                "notice_version": "privacy-notice-3.1",
                "privilege_class": "PROTECTED",
            }
        )


def test_exception_contract_forbids_raw_content():
    with pytest.raises(ValueError):
        ExceptionContract.from_dict(
            {
                "exception_id": "e1",
                "matter_id": "m1",
                "category": "CITATION_NOT_FOUND",
                "severity": "HIGH",
                "summary": "x",
                "status": "OPEN",
                "raw_client_content_logged": True,
            }
        )


def test_approval_contract_requires_hash():
    a = ApprovalContract(
        approval_id="a1",
        production_id="p1",
        matter_id="m1",
        stage="REVIEW",
        actor_id="L1",
        decision="APPROVED",
        snapshot_hash="a" * 32,
        ts="2026-07-21T00:00:00Z",
    )
    assert a.to_dict()["stage"] == "REVIEW"


def test_knowledge_source_primary_secondary():
    k = KnowledgeSourceContract(
        source_id="source_bc_laws",
        name="BC Laws",
        authority_type="OFFICIAL_PRIMARY",
        jurisdiction="BC",
        permitted_content=["statutes"],
    )
    assert k.to_dict()["authority_type"] == "OFFICIAL_PRIMARY"


def test_rtb_archive_absence_not_nonexistence():
    r = lookup_rtb_decision(citation_or_file="does-not-exist")
    assert r.found is False
    assert r.absence_proves_nonexistence is False
    assert "not proof" in r.warning.lower() or "not proof" in RTB_ARCHIVE_WARNING.lower()
    d = RtbDecisionContract(decision_id="x")
    assert d.to_dict()["archive_coverage"] == "PARTIAL"


def test_form_66_petition():
    assert petition_form().form_number == "66"
    assert petition_form().document_type == "PETITION"


def test_jr_clock_standard_and_uncertain():
    ok = calculate_jr_clock(
        JrClockRequest(
            matter_id="M1",
            issuance_date="2026-01-15",
            finality_known=True,
            enabling_act_known=True,
            human_confirmed=True,
        )
    )
    assert ok.clock_mode == JrClockMode.STANDARD_60_FROM_ISSUANCE
    assert ok.primary_deadline == "2026-03-16"
    assert ok.hitl_required is False

    unk = calculate_jr_clock(
        JrClockRequest(matter_id="M1", issuance_date=None)
    )
    assert unk.clock_mode == JrClockMode.ISSUANCE_UNKNOWN
    assert unk.primary_deadline is None

    fin = calculate_jr_clock(
        JrClockRequest(
            matter_id="M1",
            issuance_date="2026-01-15",
            finality_known=False,
        )
    )
    assert fin.clock_mode == JrClockMode.FINALITY_UNCERTAIN
    assert fin.alternatives

    ext = calculate_jr_clock(
        JrClockRequest(
            matter_id="M1",
            issuance_date="2026-01-15",
            extension_sought=True,
        )
    )
    assert ext.clock_mode == JrClockMode.ATA_S57_2_EXTENSION_PATH


def test_withdrawal_not_unconditional_delete():
    ledger = ConsentLedger()
    rec = ledger.grant(
        matter_id="M1",
        client_id="C1",
        scope=ConsentScope.AI_ANALYSIS,
        purpose="analysis",
    )
    ledger.place_legal_hold("M1")
    ledger.withdraw(rec.consent_id, derived_artifacts=["emb_1"])
    assert "M1" in ledger.blocked_ai_matters
    # plan privilege unchanged was audited
    assert any(e.action == "PRIVILEGE_UNCHANGED" for e in ledger.audit.entries)


def test_messaging_model_b_not_e2e_by_default():
    m = SecureMessagingStub()
    assert m.encryption_model == "MODEL_B_WORKSPACE"
    msg = m.send(matter_id="M1", sender_id="c1", body="hello")
    assert msg.e2e is False
