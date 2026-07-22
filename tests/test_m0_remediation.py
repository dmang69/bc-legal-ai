"""M0 critical remediation unit tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from architecture.legal_test import LegalTestDisabledError, rta_s56_retaliatory_eviction_test
from architecture.legal_test_lifecycle import LegalTestLifecycle, LifecycleRecord
from architecture.section_topic import (
    RTA_S56_REGISTRY,
    SectionTopicRecord,
    validate_section_topic,
)
from backend.api.public_demo import enforce_public_text, is_public_demo
from backend.legal_tests.evaluate import evaluate_legal_test
from services.deadlines.states import DeadlineState, calculate_deadline

ROOT = Path(__file__).resolve().parents[1]


def test_invalidation_record_exists():
    path = ROOT / "legal_knowledge" / "invalidated_tests.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["invalidations"][0]["status"] == "INVALIDATED"
    assert "s.56" in data["invalidations"][0]["reason"] or "s.56" in data["invalidations"][0]["affected_test"]


def test_s56_disabled():
    t = rta_s56_retaliatory_eviction_test()
    assert t.disabled
    with pytest.raises(LegalTestDisabledError):
        evaluate_legal_test(t, [])


def test_section_topic_blocks_retaliation_on_s56():
    r = validate_section_topic(RTA_S56_REGISTRY)
    assert r.ok is False
    assert any("retaliat" in x.lower() or "inconsistent" in x.lower() for x in r.reasons)


def test_section_topic_ok_when_aligned():
    rec = SectionTopicRecord(
        act="Residential Tenancy Act",
        section="28",
        section_heading="Quiet enjoyment",
        source_url="https://www.bclaws.gov.bc.ca/",
        expected_legal_topic="quiet_enjoyment",
        human_verifier="lawyer_demo",
        verified_at="2026-07-21",
    )
    assert validate_section_topic(rec).ok is True


def test_deadline_missing_inputs_human_review():
    r = calculate_deadline(matter_id="M1", label="JR")
    assert r.state == DeadlineState.HUMAN_REVIEW_REQUIRED
    assert r.to_dict()["definitive_for_client"] is False


def test_deadline_human_confirmed():
    r = calculate_deadline(
        matter_id="M1",
        label="JR",
        start_date="2026-01-15",
        service_method="personal",
        window_days=60,
        human_confirmed=True,
        synthetic=True,
    )
    assert r.state == DeadlineState.HUMAN_CONFIRMED
    assert r.due_date == "2026-03-16"
    assert r.synthetic is True


def test_lifecycle_active_requires_transition():
    rec = LifecycleRecord(test_id="T1", state=LegalTestLifecycle.DRAFT)
    rec.transition(LegalTestLifecycle.SOURCE_VERIFIED, actor="sys")
    rec.transition(LegalTestLifecycle.LEGAL_REVIEW, actor="sys")
    rec.transition(LegalTestLifecycle.APPROVED, actor="lawyer_1")
    rec.transition(LegalTestLifecycle.ACTIVE, actor="lawyer_1")
    assert rec.is_callable()
    with pytest.raises(ValueError):
        rec.transition(LegalTestLifecycle.DRAFT, actor="x")


def test_public_demo_text_block(monkeypatch):
    monkeypatch.setenv("APP_MODE", "public_demo")
    assert is_public_demo()
    bad = enforce_public_text("My file is VAN-S-S-123456")
    assert bad["ok"] is False
    good = enforce_public_text("I got a two month notice for landlord use")
    assert good["ok"] is True


def test_synthetic_fixture_marker():
    data = json.loads(
        (ROOT / "fixtures" / "synthetic" / "demo_matter.json").read_text(encoding="utf-8")
    )
    assert data["synthetic"] is True
    assert data["public_demo_approved"] is True
