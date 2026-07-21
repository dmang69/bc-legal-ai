"""Key-fact pairwise contradiction engine."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.evidence_node import (
    AuthenticityStatus,
    EvidenceNode,
    KeyFact,
    ResolutionStrategy,
    SourceType,
)
from backend.evidence.contradiction_engine import detect_key_fact_contradictions
from backend.evidence.nodes import EvidenceNodeStore


def _node(nid: str, facts: list[KeyFact], **kw) -> EvidenceNode:
    return EvidenceNode(
        node_id=nid,
        doc_hash=f"sha256:{nid}",
        source_type=SourceType.PHOTO,
        key_facts=facts,
        **kw,
    )


def test_shared_fact_conflicting_values():
    a = _node(
        "EV-2026-000001",
        [
            KeyFact(
                fact="Repair status",
                fact_key="mold_repaired",
                value="fixed",
                confidence=0.9,
            )
        ],
        authenticity_status=AuthenticityStatus.VERIFIED,
    )
    b = _node(
        "EV-2026-000002",
        [
            KeyFact(
                fact="Repair status",
                fact_key="mold_repaired",
                value="unfixed",
                confidence=0.7,
            )
        ],
        authenticity_status=AuthenticityStatus.UNVERIFIED,
    )
    result = detect_key_fact_contradictions([a, b], apply_edges=True)
    assert len(result.reports) == 1
    r = result.reports[0]
    assert r.fact == "mold_repaired"
    assert r.node_a_claim == "fixed"
    assert r.node_b_claim == "unfixed"
    assert r.weight_difference == abs(0.9 - 0.7)
    assert r.resolution_strategy == ResolutionStrategy.A_PRIORITY
    assert "EV-2026-000002" in a.contradicts
    assert "EV-2026-000001" in b.contradicts
    assert a.contradiction_warning is True
    assert b.contradiction_warning is True
    assert "mold_repaired" in a.contradiction_fact_keys


def test_same_value_no_contradiction():
    a = _node(
        "EV-2026-000003",
        [KeyFact(fact="served", fact_key="notice_served", value="yes", confidence=0.9)],
    )
    b = _node(
        "EV-2026-000004",
        [KeyFact(fact="served", fact_key="notice_served", value="yes", confidence=0.8)],
    )
    result = detect_key_fact_contradictions([a, b], apply_edges=True)
    assert result.reports == []
    assert a.contradiction_warning is False


def test_temporal_spread_both_relevant():
    a = _node(
        "EV-2026-000005",
        [KeyFact(fact="x", fact_key="unit_condition", value="mold present", confidence=0.8)],
        date_created="2023-06-01",
    )
    b = _node(
        "EV-2026-000006",
        [KeyFact(fact="x", fact_key="unit_condition", value="mold cleared", confidence=0.8)],
        date_created="2025-11-28",
    )
    result = detect_key_fact_contradictions([a, b], apply_edges=True)
    assert len(result.reports) == 1
    assert result.reports[0].resolution_strategy == ResolutionStrategy.BOTH_RELEVANT


def test_store_scan_persists():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        store = EvidenceNodeStore("m-c", root=root)
        a = _node(
            "EV-2026-000010",
            [KeyFact(fact="paid", fact_key="rent_paid", value="paid", confidence=0.5)],
        )
        b = _node(
            "EV-2026-000011",
            [KeyFact(fact="unpaid", fact_key="rent_paid", value="unpaid", confidence=0.5)],
        )
        a.matter_id = "m-c"
        b.matter_id = "m-c"
        store.add(a, persist=False)
        store.add(b, persist=False)
        result = store.run_contradiction_scan(persist=True)
        assert len(result.reports) == 1
        assert result.reports[0].resolution_strategy == ResolutionStrategy.NEEDS_HUMAN
        store2 = EvidenceNodeStore("m-c", root=root)
        assert store2.get("EV-2026-000010").contradiction_warning is True


if __name__ == "__main__":
    test_shared_fact_conflicting_values()
    test_same_value_no_contradiction()
    test_temporal_spread_both_relevant()
    test_store_scan_persists()
    print("OK: 4 contradiction engine tests passed")
