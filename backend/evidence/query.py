"""
Matter-scoped evidence queries.

  query_evidence(fact, min_strength, include_contradictions)
  query_timeline(start, end, event_types)
  query_gaps(claim, required_continuity)
  query_argument_support(legal_test, strategy)
"""

from __future__ import annotations

import re
from datetime import date
from typing import Iterable, Optional, Sequence

from architecture.evidence_node import EvidenceNode, SourceType
from architecture.query_api import (
    ArgumentStrategy,
    EvidenceChain,
    EvidenceQueryResult,
    TimelineEventType,
)
from architecture.timeline import GapDetectionItem, GapSignificance, TimelineEvent
from backend.evidence.contradiction_engine import detect_key_fact_contradictions
from backend.evidence.gap_detection import build_gap_detection_report
from backend.evidence.strength import apply_strength_to_node, score_to_tier
from backend.evidence.timeline_engine import build_timeline_from_nodes


def _norm(text: str) -> str:
    t = (text or "").lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _tokens(text: str) -> set[str]:
    return {w for w in _norm(text).split() if len(w) > 2}


def _fact_match_score(node: EvidenceNode, fact: str) -> float:
    """0–1 relevance of node to free-text fact query."""
    q = _tokens(fact)
    if not q:
        return 0.0
    blob_parts = [
        node.extracted_text or "",
        node.source_file or "",
        " ".join(node.claim_tags),
        " ".join(kf.fact for kf in node.key_facts),
        " ".join(kf.resolved_key() for kf in node.key_facts),
        " ".join(str(kf.value or "") for kf in node.key_facts),
    ]
    blob = _tokens(" ".join(blob_parts))
    if not blob:
        return 0.0
    inter = q & blob
    if not inter:
        # soft: any claim tag token overlap
        return 0.0
    return len(inter) / max(len(q), 1)


def _ensure_scored(nodes: Iterable[EvidenceNode]) -> None:
    for n in nodes:
        if n.strength_score is None:
            apply_strength_to_node(n)


def _node_strength(node: EvidenceNode) -> float:
    if node.strength_score is None:
        apply_strength_to_node(node)
    return float(node.strength_score or 0.0)


# --- query_evidence ---


def query_evidence(
    nodes: list[EvidenceNode],
    *,
    fact: str,
    min_strength: float = 0.5,
    include_contradictions: bool = True,
    min_fact_relevance: float = 0.2,
) -> EvidenceQueryResult:
    """
    Get evidence supporting a specific factual claim.

    Returns matching nodes (filtered by strength) and optional ContradictionReports.
    """
    _ensure_scored(nodes)
    matched: list[EvidenceNode] = []
    for n in nodes:
        rel = _fact_match_score(n, fact)
        if rel < min_fact_relevance:
            continue
        if _node_strength(n) < min_strength:
            continue
        matched.append(n)

    matched.sort(key=lambda n: (-_node_strength(n), n.node_id))

    contradictions: list[dict] = []
    if include_contradictions and matched:
        # Contradictions among matched set, plus any report involving a matched node
        run = detect_key_fact_contradictions(matched, apply_edges=False)
        contradictions = [r.to_dict() for r in run.reports]
        # Also pull stored contradiction flags against whole graph
        matched_ids = {n.node_id for n in matched}
        for n in matched:
            for other in n.contradicts:
                if other not in matched_ids:
                    contradictions.append(
                        {
                            "fact": "(edge)",
                            "node_a": n.node_id,
                            "node_b": other,
                            "node_a_claim": "",
                            "node_b_claim": "",
                            "resolution_strategy": "NEEDS_HUMAN",
                            "weight_difference": 0.0,
                            "note": "CONTRADICTS edge to node outside match set",
                        }
                    )

    return EvidenceQueryResult(
        nodes=[n.to_dict() for n in matched],
        contradictions=contradictions,
        fact_query=fact,
        min_strength=min_strength,
    )


# --- query_timeline ---

_SOURCE_TO_EVENT_TYPE: dict[SourceType, TimelineEventType] = {
    SourceType.EMAIL: TimelineEventType.COMMUNICATION,
    SourceType.TEXT_MESSAGE: TimelineEventType.COMMUNICATION,
    SourceType.GOVERNMENT_CORRESPONDENCE: TimelineEventType.NOTICE,
    SourceType.PHOTO: TimelineEventType.PHOTO_OR_MEDIA,
    SourceType.VIDEO: TimelineEventType.PHOTO_OR_MEDIA,
    SourceType.AUDIO_RECORDING: TimelineEventType.PHOTO_OR_MEDIA,
    SourceType.RTB_DECISION: TimelineEventType.OFFICIAL_ORDER,
    SourceType.COURT_ORDER: TimelineEventType.OFFICIAL_ORDER,
    SourceType.LEASE_AGREEMENT: TimelineEventType.OTHER,
    SourceType.BANK_RECORD: TimelineEventType.FINANCIAL,
    SourceType.WITNESS_STATEMENT: TimelineEventType.COMMUNICATION,
    SourceType.INSPECTION_CERT: TimelineEventType.HABITABILITY_ISSUE,
    SourceType.MEDICAL_RECORD: TimelineEventType.OTHER,
    SourceType.NEWS_ARTICLE: TimelineEventType.OTHER,
    SourceType.OTHER: TimelineEventType.OTHER,
}

_TAG_TO_EVENT_TYPE: dict[str, TimelineEventType] = {
    "mold_hazard": TimelineEventType.HABITABILITY_ISSUE,
    "non_repair": TimelineEventType.HABITABILITY_ISSUE,
    "city_enforcement": TimelineEventType.HABITABILITY_ISSUE,
    "quiet_enjoyment": TimelineEventType.HABITABILITY_ISSUE,
    "retaliatory_eviction": TimelineEventType.LEGAL_FILING,
    "official_order": TimelineEventType.OFFICIAL_ORDER,
    "rent_issue": TimelineEventType.FINANCIAL,
    "deposit": TimelineEventType.FINANCIAL,
}


def _event_types_for_timeline_event(
    ev: TimelineEvent,
    nodes_by_id: dict[str, EvidenceNode],
) -> set[TimelineEventType]:
    types: set[TimelineEventType] = set()
    for nid in ev.supporting_nodes:
        n = nodes_by_id.get(nid)
        if not n:
            continue
        types.add(_SOURCE_TO_EVENT_TYPE.get(n.source_type, TimelineEventType.OTHER))
        for t in n.claim_tags:
            if t in _TAG_TO_EVENT_TYPE:
                types.add(_TAG_TO_EVENT_TYPE[t])
    desc = (ev.event_description or "").lower()
    if "dispute" in desc or "petition" in desc or "filed" in desc:
        types.add(TimelineEventType.LEGAL_FILING)
    if "notice" in desc:
        types.add(TimelineEventType.NOTICE)
    if not types:
        types.add(TimelineEventType.OTHER)
    return types


def _parse_day(iso: Optional[str]) -> Optional[date]:
    if not iso:
        return None
    try:
        return date.fromisoformat(iso[:10])
    except ValueError:
        return None


def query_timeline(
    nodes: list[EvidenceNode],
    *,
    start: Optional[str] = None,
    end: Optional[str] = None,
    event_types: Optional[Sequence[str]] = None,
) -> list[TimelineEvent]:
    """Get timeline slice by date range and optional event type filters."""
    events = build_timeline_from_nodes(nodes)
    nodes_by_id = {n.node_id: n for n in nodes}
    start_d = _parse_day(start)
    end_d = _parse_day(end)

    want: Optional[set[str]] = None
    if event_types:
        # accept aliases
        alias = {
            "habitatability_issue": "habitability_issue",  # common typo
            "habitability": "habitability_issue",
            "filing": "legal_filing",
            "comms": "communication",
        }
        want = set()
        for t in event_types:
            key = alias.get(t.lower(), t.lower())
            want.add(key)

    out: list[TimelineEvent] = []
    for ev in events:
        if ev.timestamp:
            d = _parse_day(ev.timestamp)
            if start_d and d and d < start_d:
                continue
            if end_d and d and d > end_d:
                continue
        elif start_d or end_d:
            # undated events excluded when range is specified
            continue

        if want is not None:
            types = {t.value for t in _event_types_for_timeline_event(ev, nodes_by_id)}
            if not (types & want):
                continue
        out.append(ev)
    return out


# --- query_gaps ---

_CLAIM_TO_TAGS: dict[str, set[str]] = {
    "retaliatory eviction": {"retaliatory_eviction"},
    "retaliatory_eviction": {"retaliatory_eviction"},
    "mold": {"mold_hazard", "non_repair"},
    "mold_hazard": {"mold_hazard"},
    "habitability": {"mold_hazard", "non_repair", "quiet_enjoyment"},
    "non_repair": {"non_repair"},
    "repair": {"non_repair", "mold_hazard"},
}


def _claim_tags(claim: str) -> set[str]:
    n = _norm(claim)
    if n in _CLAIM_TO_TAGS:
        return set(_CLAIM_TO_TAGS[n])
    for key, tags in _CLAIM_TO_TAGS.items():
        if key in n or n in key:
            return set(tags)
    # fallback: snake tokens
    return {n.replace(" ", "_")} if n else set()


def query_gaps(
    nodes: list[EvidenceNode],
    *,
    claim: str,
    required_continuity: bool = True,
    timeline: Optional[list[TimelineEvent]] = None,
) -> list[GapDetectionItem]:
    """
    Gaps relevant to a claim.

    If required_continuity, only return NOTABLE/SUSPICIOUS gaps on tagged events
    (or all non-NORMAL gaps touching the claim tags).
    """
    tags = _claim_tags(claim)
    events = timeline or build_timeline_from_nodes(nodes)
    report = build_gap_detection_report(events)

    out: list[GapDetectionItem] = []
    for item in report.items:
        item_tags = set(item.claim_tags)
        # Match if gap touches claim tags OR descriptions match claim tokens
        claim_hit = bool(item_tags & tags) if tags else True
        if not claim_hit:
            blob = _norm(item.from_description + " " + item.to_description + " " + claim)
            claim_hit = any(t.replace("_", " ") in blob for t in tags) or any(
                w in blob for w in _tokens(claim)
            )
        if not claim_hit:
            continue
        if required_continuity:
            if item.gap_significance == GapSignificance.NORMAL:
                continue
        out.append(item)
    return out


# --- query_argument_support ---

_LEGAL_TEST_TAGS: list[tuple[re.Pattern[str], set[str]]] = [
    (re.compile(r"retaliat|s\.?\s*56|s56", re.I), {"retaliatory_eviction"}),
    (re.compile(r"mold|mould|habitab|repair|s\.?\s*32", re.I), {"mold_hazard", "non_repair"}),
    (re.compile(r"quiet enjoy|s\.?\s*28", re.I), {"quiet_enjoyment"}),
    (re.compile(r"entry|s\.?\s*29", re.I), {"entry"}),
    (re.compile(r"deposit|s\.?\s*38|s\.?\s*19", re.I), {"deposit"}),
    (re.compile(r"rent increase|s\.?\s*42|s\.?\s*43", re.I), {"rent_issue"}),
]


def _tags_for_legal_test(legal_test: str) -> set[str]:
    tags: set[str] = set()
    for pat, tset in _LEGAL_TEST_TAGS:
        if pat.search(legal_test):
            tags |= tset
    if not tags:
        tags = _claim_tags(legal_test)
    return tags


def query_argument_support(
    nodes: list[EvidenceNode],
    *,
    legal_test: str,
    strategy: ArgumentStrategy | str = ArgumentStrategy.MAXIMIZE_STRENGTH,
    min_strength: float = 0.4,
) -> EvidenceChain:
    """
    Build an EvidenceChain for a legal argument candidate.

    strategy:
      MAXIMIZE_STRENGTH — Tier A primary, Tier B supporting only
      MAXIMIZE_BREADTH — Tier A primary, Tier B+C supporting
    """
    if isinstance(strategy, str):
        strategy = ArgumentStrategy(strategy)

    _ensure_scored(nodes)
    tags = _tags_for_legal_test(legal_test)

    # Score relevance: claim tags + fact match to legal_test text
    scored: list[tuple[float, EvidenceNode]] = []
    for n in nodes:
        tag_hit = bool(set(n.claim_tags) & tags)
        rel = _fact_match_score(n, legal_test)
        if not tag_hit and rel < 0.15:
            continue
        strength = _node_strength(n)
        if strength < min_strength and strategy == ArgumentStrategy.MAXIMIZE_STRENGTH:
            continue
        # Combined rank
        rank = strength + (0.15 if tag_hit else 0.0) + 0.1 * rel
        scored.append((rank, n))

    scored.sort(key=lambda x: (-x[0], x[1].node_id))

    primary: list[str] = []
    supporting: list[str] = []
    for _, n in scored:
        tier = (n.strength_tier or score_to_tier(_node_strength(n)).value).upper()
        if tier == "A":
            primary.append(n.node_id)
        elif tier == "B":
            supporting.append(n.node_id)
        elif tier == "C" and strategy == ArgumentStrategy.MAXIMIZE_BREADTH:
            supporting.append(n.node_id)
        elif strategy == ArgumentStrategy.MAXIMIZE_BREADTH and _node_strength(n) >= min_strength:
            if n.node_id not in primary and n.node_id not in supporting:
                supporting.append(n.node_id)

    # If no Tier A, promote strongest B under strength strategy
    if not primary and strategy == ArgumentStrategy.MAXIMIZE_STRENGTH:
        for _, n in scored[:2]:
            if n.node_id not in primary:
                primary.append(n.node_id)
        supporting = [x for x in supporting if x not in primary]

    if strategy == ArgumentStrategy.MAXIMIZE_STRENGTH:
        # Cap supporting to top few
        supporting = supporting[:5]
        primary = primary[:5]
    else:
        supporting = supporting[:15]
        primary = primary[:8]

    chain_ids = set(primary) | set(supporting)
    chain_nodes = [n for n in nodes if n.node_id in chain_ids]

    # Gaps for related claim
    claim_for_gaps = next(iter(tags), legal_test)
    gap_items = query_gaps(nodes, claim=claim_for_gaps, required_continuity=True)
    gaps = [g.to_dict() for g in gap_items]

    # Vulnerabilities = contradictions involving chain nodes
    run = detect_key_fact_contradictions(chain_nodes or nodes, apply_edges=False)
    vulnerabilities = [
        r.to_dict()
        for r in run.reports
        if r.node_a in chain_ids or r.node_b in chain_ids
    ]
    for n in chain_nodes:
        if n.contradiction_warning:
            for other in n.contradicts:
                vulnerabilities.append(
                    {
                        "fact": "(edge)",
                        "node_a": n.node_id,
                        "node_b": other,
                        "resolution_strategy": "NEEDS_HUMAN",
                        "weight_difference": 0.0,
                        "note": "Node carries contradiction_warning",
                    }
                )

    opposing: list[str] = []
    for g in gap_items:
        if g.opposing_counsel_risk:
            opposing.append(g.opposing_counsel_risk)
        if g.gap_significance.value == "SUSPICIOUS_GAP" and g.system_prompt:
            opposing.append(f"Continuity gap: {g.system_prompt}")
    for n in chain_nodes:
        if n.hearsay_flag and not n.hearsay_exception:
            opposing.append(
                f"{n.node_id}: hearsay risk without recorded exception — anticipate objection."
            )
        if n.authenticity_status.value == "DISPUTED":
            opposing.append(f"{n.node_id}: authenticity disputed — expect challenge.")
    if not chain_nodes:
        opposing.append(
            "No evidence nodes currently map to this legal_test at the requested strength — "
            "opposing counsel may treat the ground as unsupported."
        )

    # Dedupe opposing
    seen: set[str] = set()
    opposing_unique: list[str] = []
    for o in opposing:
        if o not in seen:
            seen.add(o)
            opposing_unique.append(o)

    return EvidenceChain(
        legal_test=legal_test,
        strategy=strategy,
        primary=primary,
        supporting=supporting,
        gaps=gaps,
        vulnerabilities=vulnerabilities,
        opposing_anticipation=opposing_unique,
        min_strength_applied=min_strength,
        related_claim_tags=sorted(tags),
    )


class MatterQueryAPI:
    """Facade bound to a list of nodes (usually from MatterSession)."""

    def __init__(self, nodes: list[EvidenceNode]) -> None:
        self.nodes = list(nodes)

    def query_evidence(
        self,
        fact: str,
        *,
        min_strength: float = 0.5,
        include_contradictions: bool = True,
    ) -> EvidenceQueryResult:
        return query_evidence(
            self.nodes,
            fact=fact,
            min_strength=min_strength,
            include_contradictions=include_contradictions,
        )

    def query_timeline(
        self,
        *,
        start: Optional[str] = None,
        end: Optional[str] = None,
        event_types: Optional[Sequence[str]] = None,
    ) -> list[TimelineEvent]:
        return query_timeline(
            self.nodes, start=start, end=end, event_types=event_types
        )

    def query_gaps(
        self,
        claim: str,
        *,
        required_continuity: bool = True,
    ) -> list[GapDetectionItem]:
        return query_gaps(
            self.nodes, claim=claim, required_continuity=required_continuity
        )

    def query_argument_support(
        self,
        legal_test: str,
        *,
        strategy: ArgumentStrategy | str = ArgumentStrategy.MAXIMIZE_STRENGTH,
    ) -> EvidenceChain:
        return query_argument_support(
            self.nodes, legal_test=legal_test, strategy=strategy
        )
