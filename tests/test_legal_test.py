"""LegalTest RTA-s56-retaliatory-eviction schema and evaluation."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.evidence_node import EvidenceNode, SourceType
from architecture.legal_test import ElementStatus, rta_s56_retaliatory_eviction_test
from backend.evidence.strength import apply_strength_to_node
from backend.grounding.citation_db import CitationDB, seed_bc_workbench_citations
from backend.legal_tests.evaluate import evaluate_legal_test
from backend.matters import create_matter


def test_yaml_shape():
    t = rta_s56_retaliatory_eviction_test()
    assert t.test_id == "RTA-s56-retaliatory-eviction"
    assert t.jurisdiction == "BC"
    assert "Residential Tenancy Act" in t.source
    assert t.citation == "RTA s.56(1)"
    ids = [e.element_id for e in t.elements]
    assert ids == [
        "E1-timely-dispute",
        "E2-prior-complaint",
        "E3-temporal-nexus",
        "E4-absence-legitimate-cause",
    ]
    e1 = t.elements[0]
    assert e1.evidence_type.value == "procedural"
    assert e1.required is True
    e2 = t.elements[1]
    assert e2.evidence_type.value == "substantive"
    e3 = t.elements[2]
    assert e3.evidence_type.value == "inferential"
    assert e3.weight == 0.30
    e4 = t.elements[3]
    assert e4.required is False
    assert e4.weight == 0.40
    assert t.burden_shift is not None
    assert "E1-timely-dispute" in t.burden_shift.triggers_when_elements
    assert len(t.adverse_authority) == 2
    assert "Preston" in t.adverse_authority[0].label
    d = t.to_dict()
    assert d["id"] == "RTA-s56-retaliatory-eviction"
    assert d["burden_shift"]["reasoning_flag"] == "BURDEN_SHIFT_TO_LANDLORD"


def test_burden_shift_when_e1_e2_e3_satisfied():
    nodes = [
        EvidenceNode(
            node_id="EV-1",
            doc_hash="sha256:1",
            source_type=SourceType.OTHER,
            extracted_text="RTB dispute application filed within 10 days of notice",
            claim_tags=["retaliatory_eviction"],
            date_created="2025-11-17",
        ),
        EvidenceNode(
            node_id="EV-2",
            doc_hash="sha256:2",
            source_type=SourceType.EMAIL,
            extracted_text="Email requesting repairs for mold habitability",
            claim_tags=["non_repair", "mold_hazard", "retaliatory_eviction"],
            date_created="2025-10-01",
        ),
        EvidenceNode(
            node_id="EV-3",
            doc_hash="sha256:3",
            source_type=SourceType.GOVERNMENT_CORRESPONDENCE,
            extracted_text="Notice to End Tenancy served after complaints",
            claim_tags=["retaliatory_eviction"],
            date_created="2025-11-12",
        ),
    ]
    for n in nodes:
        apply_strength_to_node(n)
    db = seed_bc_workbench_citations(CitationDB())
    ev = evaluate_legal_test(rta_s56_retaliatory_eviction_test(), nodes, citation_db=db)
    assert ev.citation_gate_ok is False  # S56 partially verified
    by_id = {e.element_id: e for e in ev.elements}
    # E1/E2/E3 should at least partially match
    assert by_id["E1-timely-dispute"].matching_node_ids
    assert by_id["E2-prior-complaint"].matching_node_ids
    assert by_id["E3-temporal-nexus"].matching_node_ids
    # If all three satisfied → burden shift
    if all(
        by_id[x].status == ElementStatus.SATISFIED
        for x in ("E1-timely-dispute", "E2-prior-complaint", "E3-temporal-nexus")
    ):
        assert ev.burden_shift_triggered is True
        assert "BURDEN_SHIFT_TO_LANDLORD" in ev.reasoning_chain_flags
    assert any("Preston" in a or "Yu" in a for a in ev.opposing_anticipation)


def test_matter_session():
    with tempfile.TemporaryDirectory() as tmp:
        s = create_matter("LT", matter_id="mlt2", root=Path(tmp))
        s.ingest_file(
            "dispute.txt",
            b"x",
            human_notes="RTB dispute filed 5 days after notice",
        )
        s.ingest_file(
            "repair.eml",
            b"y",
            human_notes="requesting repairs mold complaint to landlord",
        )
        s.ingest_file(
            "notice.pdf",
            b"z",
            human_notes="Notice to End Tenancy",
        )
        ev = s.evaluate_legal_test("RTA-s56-retaliatory-eviction")
        assert ev.test_id == "RTA-s56-retaliatory-eviction"
        # legacy alias still works
        ev2 = s.evaluate_legal_test("TEST-RETALIATORY-EVICTION-S56")
        assert ev2.test_id == "RTA-s56-retaliatory-eviction"


if __name__ == "__main__":
    test_yaml_shape()
    test_burden_shift_when_e1_e2_e3_satisfied()
    test_matter_session()
    print("OK: 3 legal test tests passed")
