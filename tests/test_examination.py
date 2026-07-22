"""Examination outline model and synthetic cross template."""

from __future__ import annotations

from templates.examination.demo_landlord_rep_cross import demo_landlord_rep_cross


def test_synthetic_cross_no_real_names():
    o = demo_landlord_rep_cross()
    assert "Sanghera" not in o.target_witness
    assert "SYNTHETIC" in o.target_witness or "Alex" in o.target_witness
    assert o.related_legal_tests == []
