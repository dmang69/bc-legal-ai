"""GAP DETECTION REPORT — narrative gap analysis."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.evidence_node import EvidenceNode, SourceType
from architecture.timeline import GapSignificance
from backend.evidence.gap_detection import (
    build_gap_detection_report,
    format_gap_detection_report,
)
from backend.evidence.timeline_engine import build_timeline_from_nodes


def test_normal_notable_suspicious_gaps():
    nodes = [
        EvidenceNode(
            node_id="EV-2026-000001",
            doc_hash="sha256:1",
            source_type=SourceType.GOVERNMENT_CORRESPONDENCE,
            date_created="2025-11-12",
            extracted_text="Eviction notice served",
            claim_tags=["retaliatory_eviction"],
        ),
        EvidenceNode(
            node_id="EV-2026-000002",
            doc_hash="sha256:2",
            source_type=SourceType.OTHER,
            date_created="2025-11-17",
            extracted_text="Tenant files dispute",
            claim_tags=["retaliatory_eviction"],
        ),
        EvidenceNode(
            node_id="EV-2026-000003",
            doc_hash="sha256:3",
            source_type=SourceType.PHOTO,
            date_created="2025-11-28",
            extracted_text="Mold photos taken",
            claim_tags=["mold_hazard"],
        ),
        EvidenceNode(
            node_id="EV-2026-000004",
            doc_hash="sha256:4",
            source_type=SourceType.RTB_DECISION,
            date_created="2023-12-15",
            extracted_text="RTB mold decision",
            claim_tags=["mold_hazard", "official_order"],
        ),
        EvidenceNode(
            node_id="EV-2026-000005",
            doc_hash="sha256:5",
            source_type=SourceType.EMAIL,
            date_created="2025-05-10",
            extracted_text="First email to landlord",
            claim_tags=["mold_hazard", "non_repair"],
        ),
    ]
    timeline = build_timeline_from_nodes(nodes)
    report = build_gap_detection_report(timeline, matter_id="demo")
    assert report.items

    # Find 5-day normal gap Nov 12 -> Nov 17
    normal = next(
        i
        for i in report.items
        if i.from_date.startswith("2025-11-12") and i.to_date.startswith("2025-11-17")
    )
    assert normal.gap_days == 5
    assert normal.gap_significance == GapSignificance.NORMAL
    assert "Normal" in normal.analytical_question or "window" in normal.analytical_question.lower()

    # 11-day notable Nov 17 -> Nov 28 (mold continuity)
    notable = next(
        i
        for i in report.items
        if i.from_date.startswith("2025-11-17") and i.to_date.startswith("2025-11-28")
    )
    assert notable.gap_days == 11
    assert notable.gap_significance == GapSignificance.NOTABLE_GAP
    assert "worsening" in notable.analytical_question.lower() or "Upload" in notable.system_prompt
    assert "continuity" in notable.system_prompt.lower()
    text = format_gap_detection_report(report)
    assert "GAP DETECTION REPORT" in text
    assert "NOTABLE GAP" in text
    assert "SUSPICIOUS GAP" in text


def test_suspicious_multi_month_gap_prompt():
    nodes = [
        EvidenceNode(
            node_id="EV-2026-000010",
            doc_hash="sha256:a",
            source_type=SourceType.RTB_DECISION,
            date_created="2023-12-01",
            extracted_text="RTB mold decision",
            claim_tags=["mold_hazard", "official_order"],
        ),
        EvidenceNode(
            node_id="EV-2026-000011",
            doc_hash="sha256:b",
            source_type=SourceType.EMAIL,
            date_created="2025-05-01",
            extracted_text="First email to Daniel Owings",
            claim_tags=["mold_hazard", "non_repair"],
        ),
    ]
    timeline = build_timeline_from_nodes(nodes)
    report = build_gap_detection_report(timeline)
    assert len(report.items) == 1
    item = report.items[0]
    assert item.gap_significance == GapSignificance.SUSPICIOUS_GAP
    assert item.gap_days > 400
    assert "habitability" in item.system_prompt.lower() or "mold" in item.system_prompt.lower()
    assert "Opposing counsel" in item.opposing_counsel_risk
    block = item.format_block()
    assert "SUSPICIOUS GAP" in block
    assert "May" in block or "2025" in block


if __name__ == "__main__":
    test_normal_notable_suspicious_gaps()
    test_suspicious_multi_month_gap_prompt()
    print("OK: 2 gap detection tests passed")
