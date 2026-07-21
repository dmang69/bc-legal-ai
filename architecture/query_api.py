"""
Evidence query API contracts — workbench retrieval over the matter graph.

Not legal advice. legal_test strings are candidate framings; verify on BC Laws.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ArgumentStrategy(str, Enum):
    MAXIMIZE_STRENGTH = "MAXIMIZE_STRENGTH"  # prefer Tier A, fewer stronger nodes
    MAXIMIZE_BREADTH = "MAXIMIZE_BREADTH"  # include B/C for texture


class TimelineEventType(str, Enum):
    """Soft classification for timeline filtering."""

    COMMUNICATION = "communication"
    HABITABILITY_ISSUE = "habitability_issue"
    LEGAL_FILING = "legal_filing"
    NOTICE = "notice"
    PHOTO_OR_MEDIA = "photo_or_media"
    OFFICIAL_ORDER = "official_order"
    FINANCIAL = "financial"
    OTHER = "other"


@dataclass
class EvidenceChain:
    """
    Strongest evidence package for a legal argument candidate.

    legal_test is a label for the argument being supported — not a verified pin.
    """

    legal_test: str
    strategy: ArgumentStrategy
    primary: list[str] = field(default_factory=list)  # Tier A node_ids
    supporting: list[str] = field(default_factory=list)  # Tier B (+ C if breadth)
    gaps: list[dict[str, Any]] = field(default_factory=list)
    vulnerabilities: list[dict[str, Any]] = field(default_factory=list)
    opposing_anticipation: list[str] = field(default_factory=list)
    min_strength_applied: float = 0.0
    related_claim_tags: list[str] = field(default_factory=list)
    verification_note: str = (
        "legal_test and statutory pins require BC Laws / CanLII verification before filing. "
        "This chain is a workbench assembly, not a determination of legal merit."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "legal_test": self.legal_test,
            "strategy": self.strategy.value,
            "primary": list(self.primary),
            "supporting": list(self.supporting),
            "gaps": list(self.gaps),
            "vulnerabilities": list(self.vulnerabilities),
            "opposing_anticipation": list(self.opposing_anticipation),
            "min_strength_applied": self.min_strength_applied,
            "related_claim_tags": list(self.related_claim_tags),
            "verification_note": self.verification_note,
        }


@dataclass
class EvidenceQueryResult:
    nodes: list[dict[str, Any]] = field(default_factory=list)
    contradictions: list[dict[str, Any]] = field(default_factory=list)
    fact_query: str = ""
    min_strength: float = 0.0

    @property
    def count(self) -> int:
        return len(self.nodes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact": self.fact_query,
            "min_strength": self.min_strength,
            "nodes": list(self.nodes),
            "contradictions": list(self.contradictions),
            "count": self.count,
        }
