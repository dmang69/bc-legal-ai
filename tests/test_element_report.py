"""Element evaluation narrative: SUPPORTED / WEIGHTED / CONFLICTED."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.evidence_node import EvidenceNode, SourceType
from architecture.legal_test import ElementStatus, rta_s56_retaliatory_eviction_test
from backend.evidence.strength import apply_strength_to_node
from backend.grounding.citation_db import CitationDB, seed_bc_workbench_citations
from backend.legal_tests.evaluate import evaluate_legal_test


def _nodes_e2_e3_e4_conflict() -> list[EvidenceNode]:
    nodes = [
        EvidenceNode(
            node_id="EV-2026-000041",
            doc_hash="sha256:41",
            source_type=SourceType.EMAIL,
            date_created="2025-10-20",
            extracted_text="Email to landlord complaining about mold in bathroom",
            claim_tags=["mold_hazard", "non_repair", "retaliatory_eviction"],
            source_file="email_1.eml",
        ),
        EvidenceNode(
            node_id="EV-2026-000044",
            doc_hash="sha256:44",
            source_type=SourceType.EMAIL,
            date_created="2025-10-25",
            extracted_text="Second email habitability mold not fixed",
            claim_tags=["mold_hazard", "non_repair"],
            source_file="email_2.eml",
        ),
        EvidenceNode(
            node_id="EV-2026-000047",
            doc_hash="sha256:47",
            source_type=SourceType.EMAIL,
            date_created="2025-10-28",
            extracted_text="Third email to landlord about mold/habitability",
            claim_tags=["mold_hazard", "retaliatory_eviction"],
            source_file="email_3.eml",
        ),
        EvidenceNode(
            node_id="EV-2026-000062",
            doc_hash="sha256:62",
            source_type=SourceType.GOVERNMENT_CORRESPONDENCE,
            date_created="2025-11-12",
            extracted_text="Notice to End Tenancy",
            claim_tags=["retaliatory_eviction"],
            source_file="notice.pdf",
        ),
        EvidenceNode(
            node_id="EV-2026-000070",
            doc_hash="sha256:70",
            source_type=SourceType.OTHER,
            date_created="2025-09-01",
            extracted_text="RCMP letter regarding 400+ calls to the property",
            claim_tags=["city_enforcement"],
            source_file="rcmp_letter.pdf",
        ),
        EvidenceNode(
            node_id="EV-2026-000071",
            doc_hash="sha256:71",
            source_type=SourceType.OTHER,
            date_created="2025-09-15",
            extracted_text="Municipal fines totaling $6,600+",
            claim_tags=["city_enforcement"],
            source_file="fines.pdf",
        ),
        EvidenceNode(
            node_id="EV-2026-000072",
            doc_hash="sha256:72",
            source_type=SourceType.OTHER,
            date_created="2025-10-01",
            extracted_text="No convictions; shooting victim was roommate's guest",
            claim_tags=["retaliatory_eviction"],
            source_file="counter_note.txt",
        ),
        EvidenceNode(
            node_id="EV-2026-000050",
            doc_hash="sha256:50",
            source_type=SourceType.OTHER,
            date_created="2025-11-17",
            extracted_text="RTB dispute application filed within 5 days of notice",
            claim_tags=["retaliatory_eviction"],
        ),
    ]
    for n in nodes:
        apply_strength_to_node(n)
    return nodes


def test_element_report_format():
    db = seed_bc_workbench_citations(CitationDB())
    ev = evaluate_legal_test(
        rta_s56_retaliatory_eviction_test(),
        _nodes_e2_e3_e4_conflict(),
        citation_db=db,
    )
    by_id = {e.element_id: e for e in ev.elements}

    e2 = by_id["E2-prior-complaint"]
    assert e2.report_label == "SUPPORTED"
    assert e2.status == ElementStatus.SUPPORTED
    assert len(e2.matching_node_ids) >= 3
    assert "email" in e2.summary.lower() or "mold" in e2.summary.lower()

    e3 = by_id["E3-temporal-nexus"]
    assert "SUPPORTED" in e3.report_label
    assert e3.weight == 0.30
    assert e3.temporal_gap_days is not None
    assert e3.temporal_gap_days == 15  # Oct 28 -> Nov 12
    assert "15 days" in e3.temporal_gap_label
    assert e3.inference_strength == "HIGH"

    e4 = by_id["E4-absence-legitimate-cause"]
    assert e4.report_label == "CONFLICTED"
    assert e4.human_judgment_required is True
    assert e4.adverse_evidence
    assert e4.counter_evidence
    assert any("RCMP" in a or "400" in a or "calls" in a for a in e4.adverse_evidence)
    assert any("conviction" in c.lower() or "roommate" in c.lower() for c in e4.counter_evidence)

    report = ev.format_element_report()
    assert "ELEMENT E2-prior-complaint: SUPPORTED" in report
    assert "ELEMENT E3-temporal-nexus: SUPPORTED (WEIGHTED)" in report
    assert "ELEMENT E4-absence-legitimate-cause: CONFLICTED" in report
    assert "REQUIRES HUMAN JUDGMENT" in report
    assert "15 days" in report
    print(report)


if __name__ == "__main__":
    test_element_report_format()
    print("OK: element report tests passed")
