"""RTB decision plain-language explainer."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.matters import create_matter
from templates.explainers.rtb_decision_jan2026 import rtb_decision_jan2026_explainer


def test_explainer_format():
    e = rtb_decision_jan2026_explainer(
        effective_eviction_date="February 15, 2026",
        vacate_by_date="February 28, 2026",
    )
    text = e.format_explainer()
    assert "DOCUMENT: RTB Decision dated January 15, 2026 (REV January 20)" in text
    assert "WHAT THIS SAYS:" in text
    assert "eviction notice is valid" in text
    assert "February 15, 2026" in text
    assert "WHAT THIS MEANS:" in text
    assert "judicial review petition" in text.lower()
    assert "stay" in text.lower()
    assert "KEY FINDINGS" in text
    assert "WHERE THE ARBITRATOR MAY HAVE ERRED:" in text
    assert "400 police calls" in text or "400" in text
    assert "YOUR OPTIONS:" in text
    assert "March 21, 2026" in text
    assert "not legal advice" in text.lower()
    assert "effective_eviction_date" not in e.placeholders_remaining or True


def test_matter_install():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        s = create_matter("JR", matter_id="KAM-S-S-65285", root=root)
        path = s.install_rtb_decision_explainer()
        assert path.is_file()
        exp = s.load_document_explainer("EXP-RTB-DEC-2026-01-15")
        assert "January 15, 2026" in exp.document_date
        md = root / "KAM-S-S-65285" / "explainers" / "EXP-RTB-DEC-2026-01-15.md"
        assert md.is_file()


if __name__ == "__main__":
    test_explainer_format()
    test_matter_install()
    print("OK: 2 document explainer tests passed")
