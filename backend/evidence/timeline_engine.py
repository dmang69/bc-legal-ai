"""
Build TimelineEvent list from EvidenceNodes.

- Groups nodes by calendar date (date_created / date_received)
- Attaches supporting + contradicting node ids
- Computes gap_before and gap_significance between dated events
- Suggests legal_significance candidates from claim_tags (verify on BC Laws)
"""

from __future__ import annotations

import re
from datetime import date
from typing import Optional
from uuid import uuid4

from architecture.evidence_node import EvidenceNode, SourceType
from architecture.timeline import (
    GapSignificance,
    TimelineEvent,
    TimestampConfidence,
)

# Candidate issue labels only — not statute text; re-verify section pins on BC Laws
_TAG_SIGNIFICANCE: dict[str, str] = {
    "retaliatory_eviction": (
        "Candidate issue: retaliatory eviction framing — "
        "verify current RTA notice/retaliation provisions on BC Laws before reliance"
    ),
    "mold_hazard": (
        "Candidate issue: habitability / repair obligation — "
        "verify RTA repair provisions (e.g. s. 32 map in repo) on BC Laws"
    ),
    "non_repair": (
        "Candidate issue: failure to repair — verify RTA repair / order provisions on BC Laws"
    ),
    "quiet_enjoyment": (
        "Candidate issue: quiet enjoyment — official pin s. 28 (verify BC Laws; not s. 22)"
    ),
    "entry": (
        "Candidate issue: landlord entry — official pin s. 29 (verify BC Laws)"
    ),
    "deposit": (
        "Candidate issue: security deposit — verify RTA deposit provisions on BC Laws"
    ),
    "rent_issue": (
        "Candidate issue: rent / arrears / increase — verify RTA rent provisions on BC Laws"
    ),
    "city_enforcement": (
        "Candidate issue: municipal enforcement / inspection — verify bylaw source"
    ),
    "official_order": (
        "Candidate issue: tribunal/court order — verify full decision text on CanLII/RTB"
    ),
}

_SOURCE_DESC = {
    SourceType.PHOTO: "Photographic evidence captured/filed",
    SourceType.EMAIL: "Email correspondence",
    SourceType.TEXT_MESSAGE: "Text message",
    SourceType.RTB_DECISION: "RTB decision / order",
    SourceType.COURT_ORDER: "Court order",
    SourceType.INSPECTION_CERT: "Inspection certificate",
    SourceType.MEDICAL_RECORD: "Medical record",
    SourceType.LEASE_AGREEMENT: "Lease / tenancy agreement",
    SourceType.BANK_RECORD: "Bank / financial record",
    SourceType.WITNESS_STATEMENT: "Witness statement / transcript",
    SourceType.AUDIO_RECORDING: "Audio recording",
    SourceType.VIDEO: "Video evidence",
    SourceType.GOVERNMENT_CORRESPONDENCE: "Government / notice correspondence",
    SourceType.NEWS_ARTICLE: "News article",
    SourceType.OTHER: "Evidence item",
}


def _parse_day(iso: Optional[str]) -> Optional[date]:
    if not iso:
        return None
    try:
        return date.fromisoformat(iso[:10])
    except ValueError:
        m = re.search(r"(20\d{2})-(\d{2})-(\d{2})", iso)
        if m:
            try:
                return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                return None
    return None


def _node_primary_date(node: EvidenceNode) -> tuple[Optional[date], TimestampConfidence, str]:
    """Return (day, confidence, which field)."""
    if node.date_created:
        d = _parse_day(node.date_created)
        if d:
            # Full datetime with time → EXACT; date-only often APPROXIMATE
            conf = (
                TimestampConfidence.EXACT
                if "T" in node.date_created
                else TimestampConfidence.APPROXIMATE
            )
            return d, conf, "date_created"
    if node.date_received:
        d = _parse_day(node.date_received)
        if d:
            conf = (
                TimestampConfidence.EXACT
                if "T" in (node.date_received or "")
                else TimestampConfidence.APPROXIMATE
            )
            return d, conf, "date_received"
    # Filename pattern on source_file
    if node.source_file:
        m = re.search(r"(20\d{2})(\d{2})(\d{2})", node.source_file)
        if m:
            try:
                d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                return d, TimestampConfidence.APPROXIMATE, "filename"
            except ValueError:
                pass
    return None, TimestampConfidence.UNKNOWN, "none"


def _gap_label(days: int) -> str:
    if days == 1:
        return "1 day"
    return f"{days} days"


def _gap_significance(days: int) -> GapSignificance:
    if days >= 90:
        return GapSignificance.SUSPICIOUS_GAP
    if days >= 21:
        return GapSignificance.NOTABLE_GAP
    return GapSignificance.NORMAL


def _description(node: EvidenceNode) -> str:
    base = _SOURCE_DESC.get(node.source_type, "Evidence item")
    if node.extracted_text:
        snippet = node.extracted_text.strip().replace("\n", " ")
        if len(snippet) > 80:
            snippet = snippet[:77] + "…"
        return f"{base}: {snippet}"
    if node.source_file:
        return f"{base}: {node.source_file}"
    if node.key_facts:
        return f"{base}: {node.key_facts[0].fact}"
    return base


def _legal_significance(tags: list[str]) -> str:
    for t in tags:
        if t in _TAG_SIGNIFICANCE:
            return _TAG_SIGNIFICANCE[t]
    if tags:
        return f"Candidate tags: {', '.join(tags)} — verify legal framing on BC Laws / CanLII"
    return ""


def _merge_confidence(confs: list[TimestampConfidence]) -> TimestampConfidence:
    order = [
        TimestampConfidence.UNKNOWN,
        TimestampConfidence.APPROXIMATE,
        TimestampConfidence.RANGE,
        TimestampConfidence.EXACT,
    ]
    # Worst confidence among group for honesty
    best_worst = TimestampConfidence.EXACT
    for c in confs:
        if order.index(c) < order.index(best_worst):
            best_worst = c
    return best_worst if confs else TimestampConfidence.UNKNOWN


def build_timeline_from_nodes(nodes: list[EvidenceNode]) -> list[TimelineEvent]:
    """
    Produce ordered TimelineEvents.

    Same calendar day → one event with multiple supporting_nodes.
    Undated nodes → UNKNOWN timestamp events at the end.
    """
    dated: list[tuple[date, TimestampConfidence, EvidenceNode]] = []
    undated: list[EvidenceNode] = []

    for n in nodes:
        d, conf, _ = _node_primary_date(n)
        if d is None:
            undated.append(n)
        else:
            dated.append((d, conf, n))

    dated.sort(key=lambda x: (x[0], x[2].node_id))

    # Group by day
    groups: dict[date, list[tuple[TimestampConfidence, EvidenceNode]]] = {}
    for d, conf, n in dated:
        groups.setdefault(d, []).append((conf, n))

    events: list[TimelineEvent] = []
    prev_day: Optional[date] = None

    for day in sorted(groups.keys()):
        members = groups[day]
        confs = [c for c, _ in members]
        conf = _merge_confidence(confs)
        # Prefer EXACT source as timestamp_source
        source_node = members[0][1]
        for c, n in members:
            if c == TimestampConfidence.EXACT:
                source_node = n
                break

        supporting = [n.node_id for _, n in members]
        tags: list[str] = []
        for _, n in members:
            for t in n.claim_tags:
                if t not in tags:
                    tags.append(t)

        contradicting: list[str] = []
        for _, n in members:
            for c_id in n.contradicts:
                if c_id not in contradicting and c_id not in supporting:
                    contradicting.append(c_id)

        # Description: primary node + count
        if len(members) == 1:
            desc = _description(members[0][1])
        else:
            desc = (
                f"{_description(source_node)} "
                f"(+{len(members) - 1} other supporting node(s) same day)"
            )

        gap_before = None
        gap_sig = GapSignificance.NORMAL
        if prev_day is not None:
            delta = (day - prev_day).days
            gap_before = _gap_label(delta)
            gap_sig = _gap_significance(delta)

        events.append(
            TimelineEvent(
                timestamp=day.isoformat(),
                timestamp_confidence=conf,
                timestamp_source=source_node.node_id,
                event_description=desc,
                legal_significance=_legal_significance(tags),
                supporting_nodes=supporting,
                contradicting_nodes=contradicting,
                gap_before=gap_before,
                gap_significance=gap_sig,
                claim_tags=tags,
                event_id=f"TE-{uuid4().hex[:10]}",
            )
        )
        prev_day = day

    for n in undated:
        events.append(
            TimelineEvent(
                timestamp=None,
                timestamp_confidence=TimestampConfidence.UNKNOWN,
                timestamp_source=n.node_id,
                event_description=_description(n),
                legal_significance=_legal_significance(list(n.claim_tags)),
                supporting_nodes=[n.node_id],
                contradicting_nodes=list(n.contradicts),
                gap_before=None,
                gap_significance=GapSignificance.NORMAL,
                claim_tags=list(n.claim_tags),
                event_id=f"TE-{uuid4().hex[:10]}",
            )
        )

    return events


def format_timeline_markdown(events: list[TimelineEvent]) -> str:
    lines = ["## Procedural timeline (EvidenceNode-linked)", ""]
    for ev in events:
        lines.append(f"- {ev.format_line()}")
    if len(lines) == 2:
        lines.append("- *(no timeline events)*")
    lines.append("")
    lines.append(
        "> `legal_significance` is a **candidate** label only. "
        "Re-verify statute sections on **BC Laws** before filing. "
        "Gap flags (NOTABLE / SUSPICIOUS) are heuristics for human review."
    )
    return "\n".join(lines)
