"""RTB decision plain-language explainer — synthetic demo only."""

from __future__ import annotations

import tempfile
from pathlib import Path

from backend.matters import create_matter
from templates.explainers.rtb_decision_jan2026 import rtb_decision_jan2026_explainer


def test_explainer_format():
    e = rtb_decision_jan2026_explainer(
        effective_eviction_date="February 15, 2026",
        vacate_by_date="February 28, 2026",
    )
    text = e.format_explainer()
    assert "DOCUMENT:" in text
    assert "SYNTHETIC" in text
    assert "WHAT THIS SAYS:" in text
    assert "eviction notice is valid" in text
    assert "February 15, 2026" in text
    assert "WHAT THIS MEANS:" in text
    assert "judicial review" in text.lower() or "Form 66" in text
    assert "stay" in text.lower()
    assert "KEY FINDINGS" in text
    assert "WHERE THE ARBITRATOR MAY HAVE ERRED:" in text
    assert "YOUR OPTIONS:" in text
    assert "not legal advice" in text.lower()
    assert "KAM-S-S-65285" not in text


def test_matter_install():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        s = create_matter("JR", matter_id="DEMO-JR-0001", root=root)
        path = s.install_rtb_decision_explainer()
        assert path.is_file()
        exp = s.load_document_explainer("EXP-RTB-DEC-DEMO-001")
        assert "SYNTHETIC" in (exp.document_date or "")
        assert "KAM-S-S-65285" not in (exp.matter_id or "")
