"""Examination outline model and Sanghera cross template."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.examination import QuestionPurpose
from backend.matters import create_matter
from templates.examination.sanghera_cross_outline import sanghera_cross_outline


def test_sanghera_outline_shape():
    o = sanghera_cross_outline()
    assert o.target_witness == "Sukhbinder Sanghera"
    assert "Natalie" in o.goal
    assert "400 calls" in o.goal
    assert len(o.questions) == 4
    q1, q2, q3, q4 = o.questions
    assert q1.question_id == "Q1"
    assert q1.purpose == QuestionPurpose.FOUNDATIONAL
    assert q1.source_transcript and q1.source_transcript.timestamp == "02:22"
    assert q2.source_transcript and q2.source_transcript.timestamp == "63:17"
    assert "I have not entered the unit" in (q2.source_transcript.quote or "")
    assert "EM-019" in q3.source_evidence_nodes
    assert q4.source_transcript and q4.source_transcript.timestamp == "37:00"
    assert "nuisance" in q4.text.lower()
    text = o.format_outline()
    assert "EXAMINATION OUTLINE" in text
    assert "CROSS" in text
    assert "Sukhbinder" in text
    assert "Q1:" in text
    assert "Q4:" in text
    assert "Expected:" in text


def test_matter_persist_outline():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        s = create_matter("Hearing", matter_id="m-exam", root=root)
        path = s.install_sanghera_cross_template()
        assert path.is_file()
        assert "EXAM-CROSS-SANGHERA-001" in s.list_examination_outlines()
        loaded = s.load_examination_outline("EXAM-CROSS-SANGHERA-001")
        assert loaded.questions[2].source_evidence_nodes == ["EM-019"]
        md = root / "m-exam" / "examination" / "EXAM-CROSS-SANGHERA-001.md"
        assert md.is_file()
        assert "handwriting" in md.read_text(encoding="utf-8").lower()


if __name__ == "__main__":
    test_sanghera_outline_shape()
    test_matter_persist_outline()
    print("OK: 2 examination tests passed")
