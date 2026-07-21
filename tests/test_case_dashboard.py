"""Case status dashboard — KAM-S-S-65285 JR snapshot."""

from __future__ import annotations

import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.case_status import GroundStrength
from backend.matters import create_matter
from templates.case.kam_s_s_65285_dashboard import kam_s_s_65285_dashboard


def test_kam_dashboard_content():
    d = kam_s_s_65285_dashboard()
    assert d.file_number == "KAM-S-S-65285"
    assert "Judicial Review" in d.case_title
    assert d.deadline == "2026-03-21"
    assert d.evidence_complete_pct == 85
    assert d.days_remaining(as_of=date(2026, 1, 20)) == 60
    assert any("Audio" in m.label for m in d.missing_items)
    assert any("Written RTB decision" in m.label for m in d.missing_items)
    grounds = {g.label: g.strength for g in d.legal_grounds}
    assert grounds["Patent unreasonableness"] == GroundStrength.STRONG
    assert grounds["Procedural fairness violation"] == GroundStrength.MODERATE
    assert grounds["Error of law (s. 47 analysis)"] == GroundStrength.STRONG
    assert grounds["Bias"] == GroundStrength.INSUFFICIENT_EVIDENCE

    text = d.format_dashboard(as_of=date(2026, 1, 20))
    assert "YOUR CASE: Judicial Review of RTB Decision" in text
    assert "KAM-S-S-65285" in text
    assert "Petition drafting in progress" in text
    assert "60 days remaining" in text
    assert "85% complete" in text
    assert "Audio recording of RTB hearing" in text
    assert "Written RTB decision" in text
    assert "Patent unreasonableness — STRONG" in text
    assert "Bias — INSUFFICIENT EVIDENCE" in text
    assert "lawyer review" in text.lower()

    dl = d.format_deadlines(as_of=date(2026, 1, 20))
    assert "UPCOMING DEADLINES:" in dl
    assert "CRITICAL" in dl
    assert "File judicial review petition" in dl
    assert "March 21, 2026" in dl
    assert "Days remaining: 60" in dl
    assert "IMPORTANT" in dl
    assert "Request RTB hearing audio" in dl
    assert "ASAP" in dl
    assert "2-4 weeks" in dl
    assert "ROUTINE" in dl
    assert "Organize evidence binder" in dl
    assert "February 15, 2026" in dl


def test_matter_install():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        s = create_matter("JR KAM", matter_id="KAM-S-S-65285", root=root)
        path = s.install_kam_jr_case_board()
        assert path.is_file()
        board = s.format_case_board()
        assert "KAM-S-S-65285" in board
        assert (root / "KAM-S-S-65285" / "dashboard.md").is_file()


if __name__ == "__main__":
    test_kam_dashboard_content()
    test_matter_install()
    print("OK: 2 case dashboard tests passed")
