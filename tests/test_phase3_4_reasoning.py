"""Phase 3–4 — HITL packages, knowledge base, client/post-resolution."""

from __future__ import annotations

from architecture.evidence_node import PrivilegeClass, SourceType
from knowledgebase.citation_verifier import verify_citation, weight_for_jurisdiction
from knowledgebase.citation_verifier.jurisdiction import JurisdictionWeight
from knowledgebase.primary_sources import PrimarySourceRegistry
from knowledgebase.templates.catalog import list_templates
from knowledgebase.updater.monitor import UpdateMonitor
from services.consent_center import ConsentCenter
from services.jr_pipeline.service import JrPipelineStub
from services.reasoning.hitl.competency_gate import CompetencyGate, LawyerProfile
from services.reasoning.hitl.consent import ConsentLedger, ConsentScope, consent_allows_privilege_class
from services.reasoning.hitl.exceptions import ExceptionBus, Severity
from services.reasoning.hitl.privilege_check import (
    PrivilegeReviewWorkflow,
    scan_evidence_bundle,
    scan_pre_output,
)
from architecture.evidence_node import EvidenceNode
from services.retention import RetentionService
from services.client_portal import ClientPortalStub, MatterSummary


def test_consent_package_paths_and_audit():
    ledger = ConsentLedger()
    rec = ledger.grant(
        matter_id="M1", client_id="C1", scope=ConsentScope.PHOTOS
    )
    assert rec.active()
    assert ledger.audit.entries
    assert ledger.audit.entries[0].action == "GRANT"
    ledger.withdraw(rec.consent_id)
    assert ledger.requires_scope("M1", ConsentScope.PHOTOS)
    assert any(e.action == "WITHDRAW" for e in ledger.audit.entries)


def test_consent_privilege_bridge_medical():
    ledger = ConsentLedger()
    ledger.grant(matter_id="M1", client_id="C1", scope=ConsentScope.AI_ANALYSIS)
    ledger.grant(matter_id="M1", client_id="C1", scope=ConsentScope.DISCLOSE_TO_COUNSEL)
    denied = consent_allows_privilege_class(
        ledger,
        matter_id="M1",
        privilege_class=PrivilegeClass.RESTRICTED,
        source_type=SourceType.MEDICAL_RECORD,
    )
    assert denied.allowed is False
    assert any("MEDICAL" in s for s in denied.missing_scopes)
    ledger.grant(matter_id="M1", client_id="C1", scope=ConsentScope.MEDICAL_INFORMATION)
    ok = consent_allows_privilege_class(
        ledger,
        matter_id="M1",
        privilege_class=PrivilegeClass.RESTRICTED,
        source_type=SourceType.MEDICAL_RECORD,
    )
    assert ok.allowed is True


def test_exception_critical_escalates_ticket():
    bus = ExceptionBus()
    ev = bus.log_hallucination("M1", "Invented s. 999 RTA")
    assert ev.severity == Severity.CRITICAL
    assert ev.auto_escalate
    assert ev.escalation_ticket_id
    assert bus.tickets


def test_legal_test_conflicted():
    bus = ExceptionBus()
    ev = bus.log_legal_test("M1", status="CONFLICTED", test_id="RTA-s56")
    assert ev.kind.value == "LEGAL_TEST_CONFLICTED"
    assert ev.severity == Severity.CRITICAL


def test_privilege_two_factor_workflow():
    wf = PrivilegeReviewWorkflow.start(
        matter_id="M1",
        subject="Draft letter",
        body="Contains privileged solicitor-client advice.",
    )
    assert scan_pre_output(wf.body).clean is False
    ok, _ = wf.approve("lawyer-b")
    assert ok is False  # must review first
    wf.mark_reviewed("lawyer-a")
    ok, token = wf.approve("lawyer-b")
    assert ok and token


def test_bundle_scan_blocks_protected():
    node = EvidenceNode(
        node_id="EV-2026-000001",
        doc_hash="sha256:abc",
        privilege_class=PrivilegeClass.PROTECTED,
        extracted_text="ok",
    )
    r = scan_evidence_bundle([node])
    assert r.safe_to_produce is False


def test_competency_gate_rtb_not_corporate():
    lawyer = LawyerProfile(
        lawyer_id="L1",
        name="Test",
        practice_areas=["corporate"],
        jurisdictions=["BC"],
        conflict_cleared_matters=["M1"],
        bar_status="active",
        statute_currency_ack="2026-07-01",
    )
    d = CompetencyGate().evaluate(
        lawyer,
        matter_id="M1",
        required_areas=["residential_tenancy"],
    )
    assert d.allowed is False
    assert d.requires_override


def test_competency_override_with_reason():
    lawyer = LawyerProfile(
        lawyer_id="L1",
        name="Test",
        practice_areas=["residential_tenancy", "judicial_review"],
        jurisdictions=["BC"],
        conflict_cleared_matters=["M1"],
        bar_status="active",
        statute_currency_ack="2026-07-01",
        backup_reviewer_id="L2",
    )
    d = CompetencyGate().evaluate(
        lawyer,
        matter_id="M1",
        required_areas=["residential_tenancy"],
        override=True,
        override_reason="Emergency coverage; backup L2 available",
        override_by_backup=True,
    )
    # still may fail if no gaps - should pass
    assert d.allowed is True


def test_citation_verifier_rta_pin():
    v = verify_citation("RTA s. 28")
    assert v.verdict.value in ("PARTIALLY_VERIFIED", "VERIFIED")
    assert v.matched_source_id == "RTA-SBC-2002-c78"


def test_ontario_persuasive():
    f = weight_for_jurisdiction("ON")
    assert f.weight == JurisdictionWeight.PERSUASIVE


def test_point_in_time_lock():
    reg = PrimarySourceRegistry()
    reg.lock_version(
        "RTA-SBC-2002-c78",
        version_lock="pit-2025-01-01",
        current_to="January 1, 2025",
        as_of_date="2025-01-01",
    )
    lock = reg.law_as_of("RTA-SBC-2002-c78", "2025-06-01")
    assert lock is not None
    assert lock.version_lock == "pit-2025-01-01"


def test_update_monitor_change_log():
    m = UpdateMonitor()
    m.record_manual_change("RTA-SBC-2002-c78", summary="Currency re-checked", new_value="July 14, 2026")
    assert m.change_log


def test_template_catalog():
    assert any(t.form_code == "Form 66" for t in list_templates("jr"))
    assert any(t.form_code == "Form 67" for t in list_templates("jr"))


def test_consent_center():
    cc = ConsentCenter()
    cc.grant(matter_id="M1", client_id="C1", scope="TENANCY")
    state = cc.current_state("M1")
    assert "TENANCY_RECORDS" in state["active"]
    assert "explanations" in state
    cc.withdraw(matter_id="M1", scope="TENANCY")
    assert "TENANCY_RECORDS" not in cc.current_state("M1")["active"]


def test_client_portal_mfa_and_upload():
    portal = ClientPortalStub()
    s = portal.login_start("client-1")
    assert portal.mfa_verify(s.session_id, "123456")
    portal.upsert_matter(MatterSummary(matter_id="M1", title="Test"))
    draft = portal.start_upload(
        matter_id="M1", filename="mold.jpg", proposed_class="PHOTO", metadata={"date": "2026-01-01"}
    )
    assert portal.confirm_upload(draft.upload_id).status == "CONFIRMED"


def test_jr_trigger_and_petition_scaffold():
    pipe = JrPipelineStub()
    out = pipe.trigger_jr(
        matter_id="M1",
        decision_date="2026-01-15",
        error_codes=[("PROCEDURAL_FAIRNESS", "No opportunity to respond")],
    )
    assert out["clock"]["window_days"] == 60
    # Legacy top-level jr_pipeline stub may still say Form 67; post_resolution uses Form 66
    assert out["petition"]["form_code"] == "Form 66"


def test_retention_hold_blocks_destroy():
    ret = RetentionService()
    ret.place_hold("M1")
    try:
        ret.secure_destroy(
            matter_id="M1",
            object_ref="EV-1",
            classification="evidence",
            requested_by="admin",
        )
        assert False, "should block"
    except PermissionError:
        pass
    ret.release_hold("M1")
    rec = ret.secure_destroy(
        matter_id="M1",
        object_ref="EV-1",
        classification="evidence",
        requested_by="admin",
    )
    assert rec.status == "COMPLETED"
