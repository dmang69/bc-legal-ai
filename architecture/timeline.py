"""
TimelineEvent — source-linked procedural chronology unit.

Timestamps always carry confidence + the EvidenceNode that establishes the date.
Legal significance strings are candidate labels for human review — not legal advice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
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


@dataclass
class GapDetectionItem:
    """
    One inter-event gap in the GAP DETECTION REPORT.

    System prompts and opposing-counsel notes are advocacy-support heuristics
    for human review — not legal advice.
    """

    from_date: str
    from_description: str
    to_date: str
    to_description: str
    gap_label: str  # e.g. "11 days", "17 months"
    gap_days: int
    gap_significance: GapSignificance
    analytical_question: str = ""
    system_prompt: str = ""  # what to upload / document
    opposing_counsel_risk: str = ""  # how gap may be used against the party
    from_event_id: Optional[str] = None
    to_event_id: Optional[str] = None
    from_supporting_nodes: list[str] = field(default_factory=list)
    to_supporting_nodes: list[str] = field(default_factory=list)
    claim_tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_date": self.from_date,
            "from_description": self.from_description,
            "to_date": self.to_date,
            "to_description": self.to_description,
            "gap_label": self.gap_label,
            "gap_days": self.gap_days,
            "gap_significance": self.gap_significance.value,
            "analytical_question": self.analytical_question,
            "system_prompt": self.system_prompt,
            "opposing_counsel_risk": self.opposing_counsel_risk,
            "from_event_id": self.from_event_id,
            "to_event_id": self.to_event_id,
            "from_supporting_nodes": list(self.from_supporting_nodes),
            "to_supporting_nodes": list(self.to_supporting_nodes),
            "claim_tags": list(self.claim_tags),
        }

    def format_block(self) -> str:
        lines = [
            f"- {self._fmt_date(self.from_date)}: {self.from_description}",
            f"- {self._fmt_date(self.to_date)}: {self.to_description} ({self.gap_label})",
        ]
        if self.gap_significance == GapSignificance.NORMAL:
            lines.append(f"    → Normal response window")
            if self.analytical_question:
                lines.append(f"    → {self.analytical_question}")
        elif self.gap_significance == GapSignificance.NOTABLE_GAP:
            lines.append(f"    → NOTABLE GAP: {self.analytical_question or 'Review continuity.'}")
            if self.system_prompt:
                lines.append(f'    → System prompt: "{self.system_prompt}"')
        else:  # SUSPICIOUS_GAP
            lines.append(
                f"    → SUSPICIOUS GAP: System flags: \"{self.system_prompt or self.analytical_question}\""
            )
            if self.opposing_counsel_risk:
                lines.append(f"       Opposing counsel risk: {self.opposing_counsel_risk}")
        return "\n".join(lines)

    @staticmethod
    def _fmt_date(iso: str) -> str:
        """Human-friendly date for report lines."""
        try:
            d = date.fromisoformat(iso[:10])
            return d.strftime("%b %d, %Y").replace(" 0", " ")
        except ValueError:
            return iso


@dataclass
class GapDetectionReport:
    """Full GAP DETECTION REPORT for a matter timeline."""

    items: list[GapDetectionItem] = field(default_factory=list)
    matter_id: Optional[str] = None
    generated_note: str = (
        "Gap analysis is heuristic support for evidence continuity. "
        "Not legal advice. Human counsel review required."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "matter_id": self.matter_id,
            "items": [i.to_dict() for i in self.items],
            "counts": {
                "total": len(self.items),
                "normal": sum(
                    1 for i in self.items if i.gap_significance == GapSignificance.NORMAL
                ),
                "notable": sum(
                    1
                    for i in self.items
                    if i.gap_significance == GapSignificance.NOTABLE_GAP
                ),
                "suspicious": sum(
                    1
                    for i in self.items
                    if i.gap_significance == GapSignificance.SUSPICIOUS_GAP
                ),
            },
            "generated_note": self.generated_note,
        }

    def format_report(self) -> str:
        lines = ["GAP DETECTION REPORT:", ""]
        if not self.items:
            lines.append("- (no dated inter-event gaps)")
        for item in self.items:
            lines.append(item.format_block())
            lines.append("")
        lines.append(f"> {self.generated_note}")
        return "\n".join(lines).rstrip() + "\n"
