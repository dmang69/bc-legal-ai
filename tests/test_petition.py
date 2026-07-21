"""Petition outline — JR grounds structure."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.petition import JRStandardLabel
from backend.matters import create_matter
from templates.petition.rtb_jr_petition_outline import rtb_jr_petition_outline


def test_petition_structure():
    p = rtb_jr_petition_outline()
    assert p.outline_id == "PET-JR-RTB-001"
    assert len(p.grounds) == 2
    g1, g2 = p.grounds
    assert g1.title == "Patent Unreasonableness"
    assert g1.standard == JRStandardLabel.PATENT_UNREASONABLENESS
    assert [s.sub_id for s in g1.sub_grounds] == ["1a", "1b", "1c"]
    assert g2.title == "Procedural Fairness Violation"
    assert [s.sub_id for s in g2.sub_grounds] == ["2a", "2b"]

    # 1a evidence + transcript
    s1a = g1.sub_grounds[0]
    kinds = {c.kind for c in s1a.cites}
    assert "evidence" in kinds and "transcript" in kinds
    assert any(c.evidence_node_id == "EM-031" for c in s1a.cites)
    assert any(c.transcript_start == "25:40" for c in s1a.cites)

    # 1c Weichelt
    s1c = g1.sub_grounds[2]
    assert any("Weichelt" in (c.citation_short or "") for c in s1c.cites)
    assert any(c.transcript_start == "37:00" for c in s1c.cites)

    # 2a Grewal
    s2a = g2.sub_grounds[0]
    assert any("Grewal" in (c.citation_short or "") for c in s2a.cites)
    assert any(c.transcript_start == "10:21" for c in s2a.cites)

    text = p.format_outline()
    assert "GROUND 1: Patent Unreasonableness" in text
    assert "GROUND 2: Procedural Fairness" in text
    assert "EM-031" in text
    assert "400 police calls" in text or "400" in text
    assert "nuisance property" in text
    assert "Grewal" in text

    # Predicted opposition
    assert len(p.predicted_opposition) == 2
    opp = p.format_opposition_only()
    assert "PREDICTED OPPOSITION ARGUMENTS" in opp
    assert "AGAINST GROUND 1" in opp
    assert "AGAINST GROUND 2" in opp
    assert "reasonableness, not correctness" in opp
    assert "14:14" in opp
    assert "MODERATE" in opp
    assert "MODERATE-HIGH" in opp
    assert "defer to arbitrator" in opp.lower() or "defer" in opp


def test_matter_persist():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        s = create_matter("JR", matter_id="m-jr", root=root)
        path = s.install_jr_petition_template()
        assert path.is_file()
        assert "PET-JR-RTB-001" in s.list_petition_outlines()
        loaded = s.load_petition_outline("PET-JR-RTB-001")
        assert len(loaded.grounds[0].sub_grounds) == 3
        md = root / "m-jr" / "petition" / "PET-JR-RTB-001.md"
        assert md.is_file()


if __name__ == "__main__":
    test_petition_structure()
    test_matter_persist()
    print("OK: 2 petition tests passed")
