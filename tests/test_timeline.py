"""TimelineEvent builder from EvidenceNodes."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.evidence_node import EvidenceNode, SourceType
from architecture.timeline import GapSignificance, TimestampConfidence, TimelineEvent
from backend.evidence.timeline_engine import (
    build_timeline_from_nodes,
    format_timeline_markdown,
)
from backend.matters import create_matter


def test_timeline_event_shape():
    ev = TimelineEvent(
        timestamp="2025-11-12",
        timestamp_confidence=TimestampConfidence.EXACT,
        timestamp_source="EV-2026-000147",
        event_description="Landlord serves Notice to End Tenancy",
        legal_significance="Candidate issue: retaliatory eviction framing — verify on BC Laws",
        supporting_nodes=["EV-2026-000147", "EV-2026-000148"],
        contradicting_nodes=[],
        gap_before="23 days",
        gap_significance=GapSignificance.NOTABLE_GAP,
    )
    d = ev.to_dict()
    for k in (
        "timestamp",
        "timestamp_confidence",
        "timestamp_source",
        "event_description",
        "legal_significance",
        "supporting_nodes",
        "contradicting_nodes",
        "gap_before",
        "gap_significance",
    ):
        assert k in d
    assert d["timestamp_confidence"] == "EXACT"
    assert d["gap_significance"] == "NOTABLE_GAP"


def test_build_gaps_and_support():
    a = EvidenceNode(
        node_id="EV-2026-000147",
        doc_hash="sha256:a",
        source_type=SourceType.GOVERNMENT_CORRESPONDENCE,
        date_created="2025-11-12T00:00:00-08:00",
        extracted_text="Notice to End Tenancy",
        claim_tags=["retaliatory_eviction"],
        source_file="notice.pdf",
    )
    b = EvidenceNode(
        node_id="EV-2026-000148",
        doc_hash="sha256:b",
        source_type=SourceType.EMAIL,
        date_created="2025-11-12T15:00:00-08:00",
        extracted_text="Email re: same notice",
        claim_tags=["retaliatory_eviction"],
        source_file="email.eml",
    )
    c = EvidenceNode(
        node_id="EV-2026-000149",
        doc_hash="sha256:c",
        source_type=SourceType.PHOTO,
        date_created="2025-12-05",
        claim_tags=["mold_hazard"],
        source_file="20251205_mold.jpg",
    )
    events = build_timeline_from_nodes([a, b, c])
    dated = [e for e in events if e.timestamp]
    assert len(dated) == 2  # same day merged
    first = dated[0]
    assert first.timestamp == "2025-11-12"
    assert first.timestamp_confidence == TimestampConfidence.EXACT
    assert first.timestamp_source in ("EV-2026-000147", "EV-2026-000148")
    assert set(first.supporting_nodes) == {"EV-2026-000147", "EV-2026-000148"}
    second = dated[1]
    assert second.timestamp == "2025-12-05"
    assert second.gap_before == "23 days"
    assert second.gap_significance == GapSignificance.NOTABLE_GAP
    md = format_timeline_markdown(events)
    assert "2025-11-12" in md
    assert "BC Laws" in md


def test_matter_session_emits_timeline():
    with tempfile.TemporaryDirectory() as tmp:
        s = create_matter("TL", matter_id="mtl", root=Path(tmp))
        s.ingest_file(
            "20251112_notice.pdf",
            b"notice",
            human_notes="Notice to End Tenancy",
        )
        s.ingest_file(
            "20251205_photo.jpg",
            b"photo",
            human_notes="mold",
        )
        report = s.analysis_report()
        assert "timeline" in report
        assert len(report["timeline"]) >= 1
        assert (s.matter_dir / "timeline.md").is_file() or True  # written on write_report
        s.write_report()
        assert (s.matter_dir / "timeline.md").is_file()


if __name__ == "__main__":
    test_timeline_event_shape()
    test_build_gaps_and_support()
    test_matter_session_emits_timeline()
    print("OK: 3 timeline tests passed")
