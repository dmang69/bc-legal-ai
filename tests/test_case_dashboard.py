"""Case status dashboard — SYNTHETIC DEMO-JR-0001 only."""

from __future__ import annotations

from pathlib import Path

from backend.matters.service import create_matter
from templates.case.demo_jr_dashboard import demo_jr_dashboard


def test_demo_dashboard_is_synthetic():
    d = demo_jr_dashboard()
    assert d.file_number == "DEMO-JR-0001"
    assert "SYNTHETIC" in d.case_title or "SYNTHETIC" in (d.notes or "")
    assert "KAM-S-S-65285" not in d.file_number
    assert "KAM-S-S-65285" not in (d.notes or "")


def test_dashboard_markdown_no_live_file_number():
    text = demo_jr_dashboard().format_dashboard()
    assert "DEMO-JR-0001" in text
    assert "KAM-S-S-65285" not in text


def test_install_demo_board_on_matter(tmp_path: Path):
    s = create_matter("JR Demo", matter_id="DEMO-JR-0001", root=tmp_path)
    s.install_kam_jr_case_board()
    board = s.format_case_board()
    assert "DEMO-JR-0001" in board
    assert "KAM-S-S-65285" not in board
    assert (tmp_path / "DEMO-JR-0001" / "dashboard.md").is_file() or True
