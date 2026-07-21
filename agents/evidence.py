"""Evidence Analyst — matrix helpers (no OCR/LLM yet)."""

from __future__ import annotations

from architecture.schemas import EvidenceItem
from backend.evidence.crossref import (
    build_chronology,
    detect_corroboration_candidates,
    detect_temporal_conflicts,
    format_chronology_markdown,
    suggest_claim_tags,
)


def detect_gap_claims(
    claimed_tags: list[str],
    evidence: list[EvidenceItem],
) -> list[str]:
    """Return claim tags with zero supporting evidence rows."""
    covered: set[str] = set()
    for e in evidence:
        covered.update(e.claim_tags)
    return [t for t in claimed_tags if t not in covered]


def link_corroboration(a: EvidenceItem, b: EvidenceItem) -> None:
    if b.id not in a.corroborates:
        a.corroborates.append(b.id)
    if a.id not in b.corroborates:
        b.corroborates.append(a.id)


def link_contradiction(a: EvidenceItem, b: EvidenceItem) -> None:
    if b.id not in a.contradicts:
        a.contradicts.append(b.id)
    if a.id not in b.contradicts:
        b.contradicts.append(a.id)


# Re-export Layer 2 analysis helpers for agent workflows
__all__ = [
    "build_chronology",
    "detect_corroboration_candidates",
    "detect_gap_claims",
    "detect_temporal_conflicts",
    "format_chronology_markdown",
    "link_contradiction",
    "link_corroboration",
    "suggest_claim_tags",
]
