"""
GAP DETECTION REPORT — narrative inter-event gap analysis.

Builds on TimelineEvent gaps with:
  - analytical questions (was the condition worsening?)
  - system prompts (what to upload for continuity)
  - opposing-counsel risk flags on SUSPICIOUS gaps
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from architecture.timeline import (
    GapDetectionItem,
    GapDetectionReport,
    GapSignificance,
    TimelineEvent,
)


def _short_desc(ev: TimelineEvent, max_len: int = 72) -> str:
    d = (ev.event_description or "").strip()
    # Prefer first clause before colon for cleaner report lines
    if ":" in d:
        tail = d.split(":", 1)[1].strip()
        if tail:
            d = tail
    if len(d) > max_len:
        return d[: max_len - 1] + "…"
    return d or "Event"


def _gap_label_days(days: int) -> str:
    if days < 0:
        days = abs(days)
    if days >= 365:
        months = round(days / 30.44)
        if months >= 12:
            y = months // 12
            m = months % 12
            if m == 0:
                return f"{y} year" if y == 1 else f"{y} years"
            return f"{y} year{'s' if y != 1 else ''}, {m} month{'s' if m != 1 else ''}"
        return f"{months} months" if months != 1 else "1 month"
    if days >= 60:
        months = round(days / 30.44)
        return f"{months} months" if months != 1 else "1 month"
    if days == 1:
        return "1 day"
    return f"{days} days"


def _parse_day(iso: Optional[str]) -> Optional[date]:
    if not iso:
        return None
    try:
        return date.fromisoformat(iso[:10])
    except ValueError:
        return None


def _tags_set(ev: TimelineEvent) -> set[str]:
    return set(ev.claim_tags or [])


def classify_gap_significance(
    prev: TimelineEvent,
    curr: TimelineEvent,
    days: int,
) -> GapSignificance:
    """
    Gap thresholds (heuristic):

    - SUSPICIOUS: ≥ 90 days (always)
    - NOTABLE: ≥ 21 days generally; ≥ 7 days when habitability/repair tags
      are involved (continuity of condition matters for photos/repairs)
    - NORMAL: short windows (e.g. notice → dispute in 5 days)
    """
    if days >= 90:
        return GapSignificance.SUSPICIOUS_GAP
    tags = _tags_set(prev) | _tags_set(curr)
    continuity = bool(
        tags
        & {
            "mold_hazard",
            "non_repair",
            "city_enforcement",
            "quiet_enjoyment",
            "official_order",
        }
    )
    if continuity and days >= 7:
        return GapSignificance.NOTABLE_GAP
    if days >= 21:
        return GapSignificance.NOTABLE_GAP
    return GapSignificance.NORMAL


def _craft_narrative(
    prev: TimelineEvent,
    curr: TimelineEvent,
    days: int,
    significance: GapSignificance,
) -> tuple[str, str, str]:
    """
    Returns (analytical_question, system_prompt, opposing_counsel_risk).
    """
    tags = _tags_set(prev) | _tags_set(curr)
    prev_d = prev.timestamp or "?"
    curr_d = curr.timestamp or "?"
    # Human-readable range for prompts
    try:
        pd = date.fromisoformat(prev_d[:10]).strftime("%b %d, %Y").replace(" 0", " ")
        cd = date.fromisoformat(curr_d[:10]).strftime("%b %d, %Y").replace(" 0", " ")
    except ValueError:
        pd, cd = prev_d, curr_d

    moldish = bool(tags & {"mold_hazard", "non_repair", "city_enforcement"})
    noticeish = bool(tags & {"retaliatory_eviction"}) or "notice" in (
        prev.event_description + curr.event_description
    ).lower()
    disputeish = "dispute" in (prev.event_description + curr.event_description).lower()
    orderish = bool(tags & {"official_order"}) or "decision" in prev.event_description.lower()

    if significance == GapSignificance.NORMAL:
        q = "Within a typical short response / filing window."
        if noticeish and disputeish and days <= 15:
            q = "Normal response window for dispute filing after notice (confirm RTB deadlines)."
        return q, "", ""

    if significance == GapSignificance.NOTABLE_GAP:
        if moldish:
            q = "Were conditions worsening during this period?"
            prompt = (
                f"Upload any communications, photos, or observations from {pd} to {cd}. "
                "Gap weakens continuity argument."
            )
        elif noticeish:
            q = "What happened between service/filing and the next documented step?"
            prompt = (
                f"Upload any service proofs, RTB portal receipts, or correspondence from "
                f"{pd} to {cd}. Gap may be used to attack diligence or narrative continuity."
            )
        else:
            q = "What material facts occurred during this interval that are not yet on the record?"
            prompt = (
                f"Upload any communications, photos, or notes from {pd} to {cd}. "
                "Gap weakens continuity argument."
            )
        return q, prompt, ""

    # SUSPICIOUS_GAP
    if moldish or orderish:
        q = (
            "Long silence on habitability / repair after a decision or known defect — "
            "document intermediate complaints if they exist."
        )
        prompt = (
            f"Document any habitability complaints, repair requests, or mold observations "
            f"between {pd} and {cd}."
        )
        risk = (
            "Opposing counsel may argue conditions were acceptable during this period, "
            "or that the party failed to mitigate / pursue remedies promptly."
        )
    elif noticeish:
        q = "Extended gap after notice-related events requires intermediate documentation."
        prompt = (
            f"Document all steps taken between {pd} and {cd} "
            "(filings, payments, repairs, communications)."
        )
        risk = (
            "Opposing counsel may argue delay, waiver, or that intervening events "
            "break the causal narrative."
        )
    else:
        q = "Long unexplained gap in the record."
        prompt = (
            f"Document any relevant events, communications, or observations between "
            f"{pd} and {cd}."
        )
        risk = (
            "Opposing counsel may argue the silence undermines credibility or continuity "
            "of the claimed narrative."
        )
    return q, prompt, risk


def build_gap_detection_report(
    events: list[TimelineEvent],
    *,
    matter_id: Optional[str] = None,
) -> GapDetectionReport:
    """
    Walk dated timeline events in order; emit a GapDetectionItem for each consecutive pair.
    """
    dated = [e for e in events if e.timestamp and _parse_day(e.timestamp)]
    dated.sort(key=lambda e: e.timestamp or "")

    items: list[GapDetectionItem] = []
    for i in range(1, len(dated)):
        prev, curr = dated[i - 1], dated[i]
        d0, d1 = _parse_day(prev.timestamp), _parse_day(curr.timestamp)
        if not d0 or not d1:
            continue
        days = (d1 - d0).days
        if days <= 0:
            continue

        significance = classify_gap_significance(prev, curr, days)
        q, prompt, risk = _craft_narrative(prev, curr, days, significance)
        tags = sorted(_tags_set(prev) | _tags_set(curr))

        items.append(
            GapDetectionItem(
                from_date=prev.timestamp or "",
                from_description=_short_desc(prev),
                to_date=curr.timestamp or "",
                to_description=_short_desc(curr),
                gap_label=_gap_label_days(days),
                gap_days=days,
                gap_significance=significance,
                analytical_question=q,
                system_prompt=prompt,
                opposing_counsel_risk=risk,
                from_event_id=prev.event_id,
                to_event_id=curr.event_id,
                from_supporting_nodes=list(prev.supporting_nodes),
                to_supporting_nodes=list(curr.supporting_nodes),
                claim_tags=tags,
            )
        )

    return GapDetectionReport(items=items, matter_id=matter_id)


def format_gap_detection_report(report: GapDetectionReport) -> str:
    return report.format_report()
