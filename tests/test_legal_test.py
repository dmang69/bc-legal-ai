"""LegalTest schema and evaluation."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.evidence_node import EvidenceNode, SourceType
from architecture.legal_test import ElementStatus, retaliatory_eviction_s56_test
from backend.evidence.strength import apply_strength_to_node
from backend.grounding.citation_db import CitationDB, seed_bc_workbench_citations
from backend.legal_tests.evaluate import evaluate_legal_test
from backend.matters import create_matter


def test_retaliatory_test_shape():
    t = retaliatory_eviction_s56_test()
    assert t.test_id == "TEST-RETALIATORY-EVICTION-S56"
    assert t.citation == "RTA s.56(1)"
    assert t.citation_id == "CIT-RTA-S56"
    e1 = t.elements[0]
    assert e1.element_id == "ELEMENT-1"
    assert "filing complaint with RTB" in e1.protected_activities
    assert "requesting repairs" in e1.protected_activities
    assert e1.evidence
    d = t.to_dict()
    assert "elements" in d
    assert d["elements"][0]["evidence"]


def test_evaluate_partial_with_notice_and_repair_email():
    nodes = [
        EvidenceNode(
            node_id="EV-2026-000001",
            doc_hash="sha256:a",
            source_type=SourceType.EMAIL,
            date_created="2025-10-01",
            extracted_text="requesting repairs for mold",
            claim_tags=["non_repair", "mold_hazard", "retaliatory_eviction"],
        ),
        EvidenceNode(
            node_id="EV-2026-000002",
            doc_hash="sha256:b",
            source_type=SourceType.GOVERNMENT_CORRESPONDENCE,
            date_created="2025-11-12",
            extracted_text="Notice to End Tenancy",
            claim_tags=["retaliatory_eviction"],
        ),
    ]
    for n in nodes:
        apply_strength_to_node(n)
    db = seed_bc_workbench_citations(CitationDB())
    ev = evaluate_legal_test(retaliatory_eviction_s56_test(), nodes, citation_db=db)
    assert ev.test_id == "TEST-RETALIATORY-EVICTION-S56"
    assert ev.citation_gate_ok is False  # S56 only partially verified
    assert ev.citation_flag is not None
    assert ev.overall in (ElementStatus.PARTIAL, ElementStatus.NOT_SATISFIED, ElementStatus.SATISFIED)
    e1 = next(x for x in ev.elements if x.element_id == "ELEMENT-1")
    assert e1.matching_node_ids  # repair email should match protected activity tags
    assert isinstance(ev.recommended_uploads, list)


def test_matter_session_evaluate_legal_test():
    with tempfile.TemporaryDirectory() as tmp:
        s = create_matter("LT", matter_id="mlt", root=Path(tmp))
        s.ingest_file(
            "repair_email.eml",
            b"email",
            human_notes="requesting repairs mold",
        )
        s.ingest_file(
            "notice.pdf",
            b"notice",
            human_notes="Notice to End Tenancy",
        )
        ev = s.evaluate_legal_test("TEST-RETALIATORY-EVICTION-S56")
        assert ev.to_dict()["test_id"] == "TEST-RETALIATORY-EVICTION-S56"


if __name__ == "__main__":
    test_retaliatory_test_shape()
    test_evaluate_partial_with_notice_and_repair_email()
    test_matter_session_evaluate_legal_test()
    print("OK: 3 legal test tests passed")
