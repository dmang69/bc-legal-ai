"""
Evidence strength tiers — load-bearing hierarchy for case construction.

STRENGTH TIERS:
0.80–1.00 → TIER A (Primary evidence — build case around these)
0.60–0.79 → TIER B (Supporting evidence — reinforces Tier A)
0.40–0.59 → TIER C (Corroborating — adds texture but not load-bearing)
0.00–0.39 → TIER D (Weak — use only if no alternative, flag risks)

Scores are heuristic assessments for workbench ranking — not court findings.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class StrengthTier(str, Enum):
    A = "A"  # Primary
    B = "B"  # Supporting
    C = "C"  # Corroborating
    D = "D"  # Weak

    @property
    def label(self) -> str:
        return {
            StrengthTier.A: "Primary evidence — build case around these",
            StrengthTier.B: "Supporting evidence — reinforces Tier A",
            StrengthTier.C: "Corroborating — adds texture but not load-bearing",
            StrengthTier.D: "Weak — use only if no alternative, flag risks",
        }[self]

    @property
    def range_label(self) -> str:
        return {
            StrengthTier.A: "0.80–1.00",
            StrengthTier.B: "0.60–0.79",
            StrengthTier.C: "0.40–0.59",
            StrengthTier.D: "0.00–0.39",
        }[self]


def score_to_tier(score: float) -> StrengthTier:
    s = max(0.0, min(1.0, float(score)))
    if s >= 0.80:
        return StrengthTier.A
    if s >= 0.60:
        return StrengthTier.B
    if s >= 0.40:
        return StrengthTier.C
    return StrengthTier.D


@dataclass
class StrengthAssessment:
    score: float
    tier: StrengthTier
    factors: list[str]
    risks: list[str]
    guidance: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 3),
            "tier": self.tier.value,
            "tier_range": self.tier.range_label,
            "tier_label": self.tier.label,
            "factors": list(self.factors),
            "risks": list(self.risks),
            "guidance": self.guidance,
        }


def assess_score(
    score: float,
    *,
    factors: Optional[list[str]] = None,
    risks: Optional[list[str]] = None,
) -> StrengthAssessment:
    tier = score_to_tier(score)
    guidance = {
        StrengthTier.A: "Build primary case theory around this item; lead with it in submissions.",
        StrengthTier.B: "Use to reinforce Tier A exhibits; do not carry the case alone.",
        StrengthTier.C: "Texture and corroboration only; avoid load-bearing citations.",
        StrengthTier.D: "Prefer alternatives; if used, disclose risks and seek better foundation.",
    }[tier]
    extra_risks = list(risks or [])
    if tier == StrengthTier.D and "weak_tier" not in extra_risks:
        extra_risks.append("Tier_D_weak_foundation")
    return StrengthAssessment(
        score=max(0.0, min(1.0, score)),
        tier=tier,
        factors=list(factors or []),
        risks=extra_risks,
        guidance=guidance,
    )
