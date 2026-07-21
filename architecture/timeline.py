"""
TimelineEvent — source-linked procedural chronology unit.

Timestamps always carry confidence + the EvidenceNode that establishes the date.
Legal significance strings are candidate labels for human review — not legal advice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class TimestampConfidence(str, Enum):
    EXACT = "EXACT"
    RANGE = "RANGE"
    APPROXIMATE = "APPROXIMATE"
    UNKNOWN = "UNKNOWN"


class GapSignificance(str, Enum):
    NORMAL = "NORMAL"
    NOTABLE_GAP = "NOTABLE_GAP"
    SUSPICIOUS_GAP = "SUSPICIOUS_GAP"


@dataclass
class TimelineEvent:
    timestamp: Optional[str]  # ISO date or range start "YYYY-MM-DD"
    timestamp_confidence: TimestampConfidence
    timestamp_source: Optional[str]  # node_id establishing this date
    event_description: str
    legal_significance: str = ""  # candidate issue label; verify on BC Laws
    supporting_nodes: list[str] = field(default_factory=list)
    contradicting_nodes: list[str] = field(default_factory=list)
    gap_before: Optional[str] = None  # e.g. "23 days"
    gap_significance: GapSignificance = GapSignificance.NORMAL
    timestamp_end: Optional[str] = None  # for RANGE
    claim_tags: list[str] = field(default_factory=list)
    event_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "timestamp_confidence": self.timestamp_confidence.value,
            "timestamp_source": self.timestamp_source,
            "event_description": self.event_description,
            "legal_significance": self.legal_significance,
            "supporting_nodes": list(self.supporting_nodes),
            "contradicting_nodes": list(self.contradicting_nodes),
            "gap_before": self.gap_before,
            "gap_significance": self.gap_significance.value,
            "timestamp_end": self.timestamp_end,
            "claim_tags": list(self.claim_tags),
            "event_id": self.event_id,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "TimelineEvent":
        return TimelineEvent(
            timestamp=data.get("timestamp"),
            timestamp_confidence=TimestampConfidence(
                data.get("timestamp_confidence", TimestampConfidence.UNKNOWN.value)
            ),
            timestamp_source=data.get("timestamp_source"),
            event_description=str(data.get("event_description") or ""),
            legal_significance=str(data.get("legal_significance") or ""),
            supporting_nodes=list(data.get("supporting_nodes") or []),
            contradicting_nodes=list(data.get("contradicting_nodes") or []),
            gap_before=data.get("gap_before"),
            gap_significance=GapSignificance(
                data.get("gap_significance", GapSignificance.NORMAL.value)
            ),
            timestamp_end=data.get("timestamp_end"),
            claim_tags=list(data.get("claim_tags") or []),
            event_id=data.get("event_id"),
        )

    def format_line(self) -> str:
        ts = self.timestamp or "date unknown"
        conf = self.timestamp_confidence.value
        src = self.timestamp_source or "?"
        gap = f" [gap_before: {self.gap_before} · {self.gap_significance.value}]" if self.gap_before else ""
        sig = f" — *{self.legal_significance}*" if self.legal_significance else ""
        nodes = ", ".join(self.supporting_nodes) if self.supporting_nodes else src
        return f"{ts} ({conf}, src={src}) — {self.event_description}{sig} [{nodes}]{gap}"
