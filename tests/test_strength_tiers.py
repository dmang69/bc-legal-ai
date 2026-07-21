"""Evidence strength tiers A–D."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.evidence_node import (
    AdmissibilityAssessment,
    AuthenticityStatus,
    BestEvidenceRule,
    EvidenceNode,
    KeyFact,
    SourceType,
)
from architecture.strength import StrengthTier, score_to_tier
from backend.evidence.strength import compute_node_strength, format_strength_report


def test_score_to_tier_boundaries():
    assert score_to_tier(1.0) == StrengthTier.A
    assert score_to_tier(0.80) == StrengthTier.A
    assert score_to_tier(0.79) == StrengthTier.B
    assert score_to_tier(0.60) == StrengthTier.B
    assert score_to_tier(0.59) == StrengthTier.C
    assert score_to_tier(0.40) == StrengthTier.C
    assert score_to_tier(0.39) == StrengthTier.D
    assert score_to_tier(0.0) == StrengthTier.D


def test_verified_original_is_tier_a_or_b():
    n = EvidenceNode(
        node_id="EV-2026-000100",
        doc_hash="sha256:x",
        source_type=SourceType.RTB_DECISION,
        authenticity_status=AuthenticityStatus.VERIFIED,
        best_evidence_rule=BestEvidenceRule.ORIGINAL,
        key_facts=[KeyFact(fact="order issued", confidence=0.95)],
        corroborates=["EV-2026-000101", "EV-2026-000102"],
        admissibility_assessment=AdmissibilityAssessment(likely_admissible=True),
    )
    a = compute_node_strength(n)
    assert a.score >= 0.60
    assert a.tier in (StrengthTier.A, StrengthTier.B)


def test_disputed_hearsay_is_weak():
    n = EvidenceNode(
        node_id="EV-2026-000200",
        doc_hash="sha256:y",
        source_type=SourceType.TEXT_MESSAGE,
        authenticity_status=AuthenticityStatus.DISPUTED,
        best_evidence_rule=BestEvidenceRule.PHOTOCOPY,
        hearsay_flag=True,
        contradiction_warning=True,
    )
    a = compute_node_strength(n)
    assert a.tier in (StrengthTier.C, StrengthTier.D)
    assert a.score < 0.60


def test_format_report_lists_tiers():
    nodes = [
        EvidenceNode(
            node_id="EV-2026-000001",
            doc_hash="sha256:1",
            source_type=SourceType.PHOTO,
            authenticity_status=AuthenticityStatus.VERIFIED,
            best_evidence_rule=BestEvidenceRule.DIGITAL,
            strength_score=0.85,
            strength_tier="A",
            source_file="mold.jpg",
        ),
        EvidenceNode(
            node_id="EV-2026-000002",
            doc_hash="sha256:2",
            source_type=SourceType.EMAIL,
            strength_score=0.25,
            strength_tier="D",
            source_file="weak.txt",
        ),
    ]
    text = format_strength_report(nodes)
    assert "TIER A" in text
    assert "TIER D" in text
    assert "0.80–1.00" in text
    assert "EV-2026-000001" in text


if __name__ == "__main__":
    test_score_to_tier_boundaries()
    test_verified_original_is_tier_a_or_b()
    test_disputed_hearsay_is_weak()
    test_format_report_lists_tiers()
    print("OK: 4 strength tier tests passed")
