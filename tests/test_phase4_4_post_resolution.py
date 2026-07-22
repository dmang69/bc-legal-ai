"""Phase 4-4 — Full post-resolution lifecycle engine."""

from __future__ import annotations

from datetime import date, timedelta

from services.compliance.lsbc_rules import default_lsbc_rules, validate_closure
from services.post_resolution import PostResolutionStub
from services.post_resolution.compliance_monitor import ComplianceMonitor, ComplianceStatus
from services.post_resolution.destruction import DestructionService
from services.post_resolution.destruction.workflow import ClientRequestType
from services.post_resolution.enforcement import EnforcementPackager
from services.post_resolution.escalation_router import EscalationPath, EscalationRouter
from services.post_resolution.jr_pipeline import JrPipeline
from services.post_resolution.obligation_parser import parse_decision_text
from services.post_resolution.outcome_tracker import OutcomeTracker
from services.post_resolution.retention import RetentionCategory, RetentionScheduleEngine
from services.post_resolution.stay_generator import StayGenerator


SAMPLE_DECISION = """
Residential Tenancy Branch Decision dated 2026-01-15.
The landlord shall pay the tenant $1,200.00 within 15 days.
The landlord must repair the bathroom mold within 30 days.
The tenant must vacate by March 1, 2026.
"""


def test_obligation_parser_classes():
    p = parse_decision_text(SAMPLE_DECISION, matter_id="M1", decision_date="2026-01-15")
    kinds = {o.kind.value for o in p.obligations}
    assert "MONETARY" in kinds
    assert "REPAIR" in kinds
    assert "VACATE" in kinds or "POSSESSION" in kinds
    assert p.hitl_required  # always careful


def test_outcome_tracker_clocks_and_prediction():
    tr = OutcomeTracker()
    tr.set_prediction(
        "M1",
        summary="Expect repair order",
        classes=["REPAIR_ORDER"],
    )
    rec = tr.ingest_decision_text(
        matter_id="M1", text=SAMPLE_DECISION, decision_date="2026-01-15"
    )
    assert rec.clocks
    assert any("remediat" in c.label.lower() or "repair" in c.label.lower() or "within" in c.label.lower()
               for c in rec.clocks)
    assert rec.comparison is not None
    assert rec.comparison.match is False
    assert rec.comparison.failure_mode_tags


def test_compliance_reminders_and_missed_deadline():
    tr = OutcomeTracker()
    rec = tr.ingest_decision_text(
        matter_id="M1", text=SAMPLE_DECISION, decision_date="2026-01-15"
    )
    mon = ComplianceMonitor()
    mon.seed_from_tracker(tr, "M1")
    # Force a due date in the past on first clock
    rec.clocks[0].due_date = (date.today() - timedelta(days=2)).isoformat()
    events = mon.detect_non_compliance("M1", rec.clocks, today=date.today())
    assert events
    assert events[0].kind.value == "MISSED_DEADLINE"
    mon.mark_status("M1", rec.obligations[0].obligation_id, ComplianceStatus.PARTIAL)
    mon.add_evidence(
        matter_id="M1",
        obligation_id=rec.obligations[0].obligation_id,
        kind="photo",
        filename="bath.jpg",
        note="partial work only",
    )
    rems = mon.generate_reminders(
        "M1",
        [type(rec.clocks[0])(
            **{**rec.clocks[0].__dict__, "due_date": (date.today() + timedelta(days=3)).isoformat(), "status": "OPEN"}
        )],
        today=date.today(),
    )
    assert rems


def test_escalation_router_paths():
    from services.post_resolution.compliance_monitor.monitor import (
        NonComplianceEvent,
        NonComplianceKind,
    )

    router = EscalationRouter()
    evt = NonComplianceEvent(
        event_id="E1",
        matter_id="M1",
        obligation_id="O1",
        kind=NonComplianceKind.MISSED_DEADLINE,
        message="missed pay",
    )
    t = router.route_event(evt, obligation_kind="MONETARY", monetary=True)
    assert t.path in (EscalationPath.PROVINCIAL_COURT, EscalationPath.GARNISHMENT)
    t2 = router.route_event(
        NonComplianceEvent(
            event_id="E2",
            matter_id="M1",
            obligation_id="O2",
            kind=NonComplianceKind.MISSED_DEADLINE,
            message="no repair",
        ),
        obligation_kind="REPAIR",
    )
    assert t2.path == EscalationPath.RTB_ENFORCEMENT


def test_enforcement_packages():
    pack = EnforcementPackager()
    assert pack.build_rtb_enforcement("M1").documents
    assert pack.build_provincial_court_monetary("M1", amount=1200).package_type.value == "PROVINCIAL_COURT_MONETARY"
    assert pack.build_garnishment("M1").checklist


def test_jr_pipeline_and_stay():
    jr = JrPipeline()
    out = jr.trigger(
        matter_id="M1",
        decision_date="2026-01-15",
        decision_or_notes_text="No opportunity to respond; unreasonable findings.",
        client_role="tenant",
        outcome_classes=["POSSESSION_ORDER"],
    )
    assert out["unfavorable_trigger"] is True
    assert out["clock"]["window_days"] == 60
    assert out["petition"]["form_code"] == "Form 66"
    assert out["evidence_binder"]["tabs"]
    grounds = [e["ground"] for e in out["errors"]]
    assert "PROCEDURAL_FAIRNESS" in grounds or "REASONABLENESS" in grounds

    stay = StayGenerator().generate("M1", vacate_date="2026-03-01")
    assert "serious" in stay.serious_question.lower() or "[" in stay.serious_question


def test_retention_closure_and_destruction():
    eng = RetentionScheduleEngine()
    plan = eng.close_matter(
        matter_id="M1",
        closed_on="2026-07-01",
        final_summary="Matter concluded after RTB decision.",
        object_refs={"EVIDENCE": ["EV-1"], "PRIVILEGED": ["PRIV-1"]},
    )
    assert plan.privilege_lock and plan.access_frozen
    v = validate_closure(
        final_summary=plan.final_summary,
        retention_plan=plan.retention_plan,
        privilege_lock=plan.privilege_lock,
        access_frozen=plan.access_frozen,
        client_notified=True,
    )
    assert v.ok

    dest = DestructionService(schedule=eng)
    eng.place_hold("M1")
    try:
        dest.destroy(matter_id="M1", object_ref="EV-1", classification="EVIDENCE", requested_by="admin")
        assert False
    except PermissionError:
        pass
    eng.release_hold("M1")
    rec = dest.destroy(
        matter_id="M1",
        object_ref="EV-1",
        classification="EVIDENCE",
        requested_by="admin",
    )
    assert rec.method.value == "CRYPTO_SHRED"
    req = dest.client_request(
        matter_id="M1",
        client_id="C1",
        request_type=ClientRequestType.RETURN_DOCUMENTS,
        reason="client wants copies",
    )
    assert req.status == "PENDING_LAWYER"


def test_lsbc_rules_defaults():
    r = default_lsbc_rules()
    assert r.min_evidence_years >= 1
    assert "Privileged" in r.privilege_handling


def test_full_engine_facade():
    engine = PostResolutionStub()
    out = engine.ingest_decision(
        matter_id="M1",
        text=SAMPLE_DECISION,
        decision_date="2026-01-15",
        predicted_summary="Monetary only",
        predicted_classes=["MONETARY_AWARD"],
    )
    assert out["clocks"]
    assert out["comparison"] is not None
