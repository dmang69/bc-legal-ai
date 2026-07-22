"""Phase 2.1 — ingestion, classifier, confidence, transcription stubs."""

from __future__ import annotations

from architecture.evidence_node import PrivilegeClass
from middleware.privilege_guard import GuardContext, PrivilegeGuard
from services.classifier.service import DocumentClass, classify_document
from services.common.confidence import score_confidence
from services.compliance.legal_retrieval import FailClosedRetrieval
from services.compliance.no_weights import NoWeightsGuard, WeightsPolicy
from services.ingestion.service import IngestRequest, ingest_document
from services.reasoning.hitl.consent import ConsentLedger, ConsentScope
from services.reasoning.hitl.exceptions import ExceptionBus, ExceptionKind, Severity
from services.reasoning.privilege_check.service import scan_pre_output
from services.transcription.service import transcribe_audio_stub


def test_classify_rtb_decision():
    r = classify_document(
        filename="decision.pdf",
        text="Residential Tenancy Branch decision of the arbitrator.",
    )
    assert r.label == DocumentClass.RTB_DECISION
    assert r.confidence >= 0.75


def test_classify_photo_by_extension():
    r = classify_document(filename="mold.jpg", text="")
    assert r.label == DocumentClass.PHOTO


def test_confidence_hitl_on_low_scores():
    score, hitl = score_confidence(classification=0.5, extraction=0.9)
    assert hitl.required
    assert score.overall == 0.5


def test_ingest_email_with_metadata():
    text = "From: landlord@example.com\nTo: tenant@example.com\nSubject: Notice\nDate: 2026-07-01\nPlease pay rent."
    res = ingest_document(
        IngestRequest(
            filename="notice.eml",
            data=text.encode("utf-8"),
            matter_id="MAT-TEST",
            text_hint=text,
            custodian="client",
        )
    )
    assert res.doc_hash.startswith("sha256:")
    assert res.metadata.sender is not None
    assert res.node_draft is not None
    assert res.node_draft.matter_id == "MAT-TEST"


def test_ingest_exact_duplicate():
    data = b"same-bytes"
    bare = __import__("hashlib").sha256(data).hexdigest()
    res = ingest_document(
        IngestRequest(
            filename="a.pdf",
            data=data,
            matter_id="M1",
            text_hint="hello world " * 20,
            known_hashes={bare},
        )
    )
    assert res.status == "DUPLICATE"


def test_transcription_stub_requires_hitl():
    t = transcribe_audio_stub(b"\x00\x01fake", filename="hearing.mp3")
    assert t.hitl_required
    assert t.engine == "stub"


def test_fail_closed_statute_from_weights():
    d = FailClosedRetrieval().authorize_statute_text(from_model_weights=True)
    assert d.allowed is False


def test_fail_closed_bc_laws_host():
    d = FailClosedRetrieval().authorize_statute_text(
        source_url="https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/02078_01"
    )
    assert d.allowed is True


def test_no_weights_public_demo():
    g = NoWeightsGuard(mode=WeightsPolicy.PUBLIC_DEMO)
    ok, _ = g.check_request(wants_inference=True, wants_statute_from_model=False)
    assert ok is False
    assert g.may_quote_statute_from_model() is False


def test_privilege_guard_blocks_export():
    guard = PrivilegeGuard()
    r = guard.check(
        GuardContext(
            matter_id="M1",
            actor_id="u1",
            operation="export",
            privilege_class=PrivilegeClass.PROTECTED,
            production_gate_cleared=False,
        )
    )
    assert r.allowed is False


def test_consent_ledger_withdraw():
    ledger = ConsentLedger()
    rec = ledger.grant(
        matter_id="M1", client_id="C1", scope=ConsentScope.MEDICAL
    )
    assert ledger.requires_scope("M1", ConsentScope.MEDICAL) is False
    ledger.withdraw(rec.consent_id)
    assert ledger.requires_scope("M1", ConsentScope.MEDICAL) is True


def test_exception_bus_escalates():
    bus = ExceptionBus()
    ev = bus.emit(
        matter_id="M1",
        kind=ExceptionKind.HALLUCINATION_ATTEMPT,
        severity=Severity.CRITICAL,
        message="Model attempted invented section",
    )
    assert ev.auto_escalate
    assert len(bus.open_escalations("M1")) == 1


def test_privilege_pre_output_scan():
    r = scan_pre_output("This is privileged solicitor-client advice.")
    assert r.clean is False
    assert r.two_factor_required
