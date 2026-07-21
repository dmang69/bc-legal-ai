"""Tenancy dispute intake tree and deadline calculation."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.intake import (
    NoticeType,
    ServiceMethod,
    TenancyIntake,
    calculate_dispute_deadline,
    completeness_check,
)
from backend.matters import create_matter


def test_deadline_two_month():
    d, note, days = calculate_dispute_deadline(
        "2025-11-12",
        NoticeType.TWO_MONTH,
        method=ServiceMethod.PERSONAL,
    )
    assert days == 15
    assert d == "2025-11-27"
    assert "15" in note


def test_deadline_ten_day():
    d, note, days = calculate_dispute_deadline(
        "2025-11-12", NoticeType.TEN_DAY, method=ServiceMethod.MAILED
    )
    assert days == 5
    assert d == "2025-11-17"
    assert "MAILED" in note or "deemed" in note.lower()


def test_intake_tree_and_matter():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        s = create_matter("Intake test", matter_id="m-in", root=root)
        intake = s.intake_from_answers(
            {
                "property_address": "990 Example Ave",
                "unit_designation": "990",
                "tenancy_start_date": "2016-01-01",
                "current_rent": "1450",
                "lease_names": ["Tenant", "Natalie"],
                "notice_received": True,
                "notice_date_received": "2025-11-12",
                "notice_method": "personal",
                "notice_type": "two_month",
                "dispute_filed": False,
                "issue_categories": ["habitability", "repairs"],
                "issue_start": "2023-06-01",
                "issue_ongoing": True,
                "landlord_notified": True,
                "landlord_notified_how": "email",
                "landlord_notified_when": "2025-10-28",
                "issue_evidence": ["photos/", "emails/"],
            }
        )
        assert intake.notice.dispute_deadline == "2025-11-27"
        assert "property_address" not in completeness_check(intake)
        tree = intake.format_tree()
        assert "INTAKE: Tenancy Dispute" in tree
        assert "990" in tree
        assert "Natalie" in tree
        assert "2025-11-27" in tree
        loaded = s.load_tenancy_intake()
        assert loaded.unit_designation == "990"
        assert (root / "m-in" / "intake.json").is_file()
        assert (root / "m-in" / "intake_tree.md").is_file()
        assert "habitability" in s.meta.claimed_tags or "repairs" in s.meta.claimed_tags


if __name__ == "__main__":
    test_deadline_two_month()
    test_deadline_ten_day()
    test_intake_tree_and_matter()
    print("OK: 3 intake tests passed")
