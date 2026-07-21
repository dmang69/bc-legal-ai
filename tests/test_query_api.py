"""Evidence query API — fact, timeline, gaps, argument support."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.evidence_node import (
    AuthenticityStatus,
    BestEvidenceRule,
    EvidenceNode,
    KeyFact,
    SourceType,
)
from architecture.query_api import ArgumentStrategy
from backend.evidence.query import (
    MatterQueryAPI,
    query_argument_support,
    query_evidence,
    query_gaps,
    query_timeline,
)
from backend.evidence.strength import apply_strength_to_node
from backend.matters import create_matter


def _nodes_fixture() -> list[EvidenceNode]:
    nodes = [
        EvidenceNode(
            node_id="EV-2026-000147",
            doc_hash="sha256:a",
            source_type=SourceType.PHOTO,
            date_created="2025-11-28",
            extracted_text="mold present in unit as of November 2025",
            claim_tags=["mold_hazard"],
            key_facts=[
                KeyFact(
                    fact="mold present in unit as of November 2025",
                    fact_key="mold_present",
                    value="present november 2025",
                    confidence=0.95,
                )
            ],
            authenticity_status=AuthenticityStatus.VERIFIED,
            best_evidence_rule=BestEvidenceRule.DIGITAL,
            source_file="20251128_mold.jpg",
        ),
        EvidenceNode(
            node_id="EV-2026-000148",
            doc_hash="sha256:b",
            source_type=SourceType.EMAIL,
            date_created="2025-11-20",
            extracted_text="email describing black mold in bathroom",
            claim_tags=["mold_hazard", "non_repair"],
            authenticity_status=AuthenticityStatus.UNVERIFIED,
            source_file="email_mold.eml",
        ),
        EvidenceNode(
            node_id="EV-2026-000149",
            doc_hash="sha256:c",
            source_type=SourceType.GOVERNMENT_CORRESPONDENCE,
            date_created="2025-11-12",
            extracted_text="Notice to End Tenancy",
            claim_tags=["retaliatory_eviction"],
            source_file="notice.pdf",
        ),
        EvidenceNode(
            node_id="EV-2026-000150",
            doc_hash="sha256:d",
            source_type=SourceType.RTB_DECISION,
            date_created="2023-12-01",
            extracted_text="RTB mold decision",
            claim_tags=["mold_hazard", "official_order"],
            authenticity_status=AuthenticityStatus.VERIFIED,
            best_evidence_rule=BestEvidenceRule.CERTIFIED_COPY,
        ),
        EvidenceNode(
            node_id="EV-2026-000151",
            doc_hash="sha256:e",
            source_type=SourceType.EMAIL,
            date_created="2025-05-10",
            extracted_text="First email requesting mold repair",
            claim_tags=["mold_hazard", "non_repair"],
        ),
    ]
    for n in nodes:
        apply_strength_to_node(n)
    return nodes


def test_query_evidence_by_fact():
    nodes = _nodes_fixture()
    result = query_evidence(
        nodes,
        fact="mold present in unit as of November 2025",
        min_strength=0.5,
        include_contradictions=True,
    )
    assert result.count >= 1
    ids = {n["node_id"] for n in result.nodes}
    assert "EV-2026-000147" in ids
    d = result.to_dict()
    assert d["min_strength"] == 0.5


def test_query_timeline_slice():
    nodes = _nodes_fixture()
    events = query_timeline(
        nodes,
        start="2025-05-01",
        end="2025-12-01",
        event_types=["communication", "habitability_issue", "legal_filing", "notice"],
    )
    assert events
    for e in events:
        assert e.timestamp is not None
        assert e.timestamp >= "2025-05-01"
        assert e.timestamp <= "2025-12-01"


def test_query_gaps_retaliatory():
    nodes = _nodes_fixture()
    # long gap Dec 2023 -> May 2025 should appear for mold claim continuity
    gaps = query_gaps(nodes, claim="mold", required_continuity=True)
    assert any(g.gap_significance.value in ("NOTABLE_GAP", "SUSPICIOUS_GAP") for g in gaps)


def test_query_argument_support_strength():
    nodes = _nodes_fixture()
    chain = query_argument_support(
        nodes,
        legal_test="s.56 RTA retaliatory eviction",
        strategy=ArgumentStrategy.MAXIMIZE_STRENGTH,
    )
    d = chain.to_dict()
    assert d["legal_test"].startswith("s.56")
    assert d["strategy"] == "MAXIMIZE_STRENGTH"
    assert "retaliatory_eviction" in d["related_claim_tags"]
    assert "verification_note" in d
    # notice node should be in primary or supporting
    all_ids = set(chain.primary) | set(chain.supporting)
    assert "EV-2026-000149" in all_ids


def test_query_argument_support_breadth_mold():
    nodes = _nodes_fixture()
    chain = query_argument_support(
        nodes,
        legal_test="RTA repair / mold habitability",
        strategy="MAXIMIZE_BREADTH",
    )
    all_ids = set(chain.primary) | set(chain.supporting)
    assert "EV-2026-000147" in all_ids or "EV-2026-000150" in all_ids
    assert isinstance(chain.gaps, list)
    assert isinstance(chain.vulnerabilities, list)
    assert isinstance(chain.opposing_anticipation, list)


def test_matter_session_query_methods():
    with tempfile.TemporaryDirectory() as tmp:
        s = create_matter("Q", matter_id="mq", root=Path(tmp))
        s.ingest_file(
            "20251128_mold.jpg",
            b"photo",
            human_notes="mold present in unit november 2025",
        )
        s.ingest_file(
            "notice_end.pdf",
            b"notice",
            human_notes="Notice to End Tenancy after complaints",
        )
        r = s.query_evidence("mold present", min_strength=0.0)
        assert r.count >= 1
        tl = s.query_timeline(start="2025-01-01", end="2026-01-01")
        assert isinstance(tl, list)
        chain = s.query_argument_support(
            "retaliatory eviction", strategy="MAXIMIZE_STRENGTH"
        )
        assert chain.to_dict()["strategy"] == "MAXIMIZE_STRENGTH"


if __name__ == "__main__":
    test_query_evidence_by_fact()
    test_query_timeline_slice()
    test_query_gaps_retaliatory()
    test_query_argument_support_strength()
    test_query_argument_support_breadth_mold()
    test_matter_session_query_methods()
    print("OK: 6 query API tests passed")
