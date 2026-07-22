"""
Decision text → structured obligations (heuristic skeleton).

Production: OCR + lawyer-verified extraction. Fail-closed → HITL on low confidence.
Not legal advice. Confirm every obligation against the signed order / decision PDF.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class ObligationKind(str, Enum):
    MONETARY = "MONETARY"
    REPAIR = "REPAIR"
    CONDUCT = "CONDUCT"
    VACATE = "VACATE"
    POSSESSION = "POSSESSION"
    DISMISSAL = "DISMISSAL"
    OTHER = "OTHER"


class OutcomeClass(str, Enum):
    MONETARY_AWARD = "MONETARY_AWARD"
    REPAIR_ORDER = "REPAIR_ORDER"
    CONDUCT_ORDER = "CONDUCT_ORDER"
    DISMISSAL = "DISMISSAL"
    POSSESSION_ORDER = "POSSESSION_ORDER"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


@dataclass
class Obligation:
    obligation_id: str
    kind: ObligationKind
    party: str  # landlord | tenant | both | unknown
    description: str
    amount: Optional[float] = None
    currency: str = "CAD"
    deadline_days: Optional[int] = None
    deadline_date: Optional[str] = None  # ISO if known
    confidence: float = 0.0
    source_span: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "obligation_id": self.obligation_id,
            "kind": self.kind.value,
            "party": self.party,
            "description": self.description,
            "amount": self.amount,
            "currency": self.currency,
            "deadline_days": self.deadline_days,
            "deadline_date": self.deadline_date,
            "confidence": self.confidence,
            "source_span": self.source_span,
        }


@dataclass
class ParsedDecision:
    matter_id: str
    decision_date: Optional[str]
    outcome_classes: list[OutcomeClass]
    obligations: list[Obligation]
    raw_excerpt: str = ""
    overall_confidence: float = 0.0
    hitl_required: bool = True
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "matter_id": self.matter_id,
            "decision_date": self.decision_date,
            "outcome_classes": [c.value for c in self.outcome_classes],
            "obligations": [o.to_dict() for o in self.obligations],
            "raw_excerpt": self.raw_excerpt[:2000],
            "overall_confidence": self.overall_confidence,
            "hitl_required": self.hitl_required,
            "notes": list(self.notes),
        }


_MONEY = re.compile(
    r"(?:pay|award(?:ed)?|order(?:ed)?\s+to\s+pay|shall\s+pay)\s+"
    r"(?:the\s+)?(?:landlord|tenant|applicant|respondent)?\s*"
    r"\$?\s*([\d,]+(?:\.\d{2})?)",
    re.I,
)
_REPAIR = re.compile(
    r"(?:repair|remediat(?:e|ion)|fix\s+the|make\s+good|restore)\b[^.]{0,120}",
    re.I,
)
_VACATE = re.compile(
    r"(?:vacate|give\s+up\s+possession|order\s+of\s+possession|"
    r"possession\s+(?:is\s+)?granted|must\s+leave)\b[^.]{0,120}",
    re.I,
)
_CONDUCT = re.compile(
    r"(?:must\s+not|cease|refrain|conduct\s+order|quiet\s+enjoyment|"
    r"shall\s+not\s+enter)\b[^.]{0,120}",
    re.I,
)
_DISMISS = re.compile(r"\b(dismiss(?:ed|al)|application\s+is\s+dismissed)\b", re.I)
_DAYS = re.compile(r"\bwithin\s+(\d+)\s+days?\b", re.I)
_BY_DATE = re.compile(
    r"\bby\s+((?:january|february|march|april|may|june|july|august|september|"
    r"october|november|december)\s+\d{1,2},?\s+20\d{2}|\d{4}-\d{2}-\d{2})\b",
    re.I,
)
_DEC_DATE = re.compile(
    r"\b(?:dated|decision\s+date|made\s+on)\s*:?\s*"
    r"(\d{4}-\d{2}-\d{2}|(?:january|february|march|april|may|june|july|august|"
    r"september|october|november|december)\s+\d{1,2},?\s+20\d{2})\b",
    re.I,
)


def _oid() -> str:
    return f"OBL-{uuid4().hex[:10]}"


def _parse_amount(s: str) -> float:
    return float(s.replace(",", ""))


def parse_decision_text(
    text: str,
    *,
    matter_id: str,
    decision_date: Optional[str] = None,
) -> ParsedDecision:
    """
    Heuristic parse of decision/order text. Always sets hitl_required unless
    confidence is high and structure is unambiguous (still recommend human check).
    """
    body = text or ""
    notes: list[str] = [
        "Heuristic parse only — verify against official decision PDF.",
        "PDF binary ingest is not performed here; pass extracted text or OCR output.",
    ]
    obligations: list[Obligation] = []
    classes: list[OutcomeClass] = []

    if not decision_date:
        m = _DEC_DATE.search(body)
        if m:
            decision_date = m.group(1)

    for m in _MONEY.finditer(body):
        span = m.group(0)
        party = "landlord" if re.search(r"\blandlord\b", span, re.I) else (
            "tenant" if re.search(r"\btenant\b", span, re.I) else "unknown"
        )
        days_m = _DAYS.search(body[m.start() : m.start() + 200])
        obligations.append(
            Obligation(
                obligation_id=_oid(),
                kind=ObligationKind.MONETARY,
                party=party,
                description=span.strip(),
                amount=_parse_amount(m.group(1)),
                deadline_days=int(days_m.group(1)) if days_m else None,
                confidence=0.75,
                source_span=span[:200],
            )
        )
        if OutcomeClass.MONETARY_AWARD not in classes:
            classes.append(OutcomeClass.MONETARY_AWARD)

    for m in _REPAIR.finditer(body):
        span = m.group(0).strip()
        days_m = _DAYS.search(span) or _DAYS.search(body[m.start() : m.start() + 180])
        date_m = _BY_DATE.search(body[m.start() : m.start() + 180])
        obligations.append(
            Obligation(
                obligation_id=_oid(),
                kind=ObligationKind.REPAIR,
                party="landlord",
                description=span,
                deadline_days=int(days_m.group(1)) if days_m else None,
                deadline_date=date_m.group(1) if date_m else None,
                confidence=0.7,
                source_span=span[:200],
            )
        )
        if OutcomeClass.REPAIR_ORDER not in classes:
            classes.append(OutcomeClass.REPAIR_ORDER)

    for m in _VACATE.finditer(body):
        span = m.group(0).strip()
        days_m = _DAYS.search(span) or _DAYS.search(body[m.start() : m.start() + 180])
        date_m = _BY_DATE.search(body[m.start() : m.start() + 180])
        obligations.append(
            Obligation(
                obligation_id=_oid(),
                kind=ObligationKind.VACATE
                if re.search(r"vacate|leave", span, re.I)
                else ObligationKind.POSSESSION,
                party="tenant",
                description=span,
                deadline_days=int(days_m.group(1)) if days_m else None,
                deadline_date=date_m.group(1) if date_m else None,
                confidence=0.72,
                source_span=span[:200],
            )
        )
        if OutcomeClass.POSSESSION_ORDER not in classes:
            classes.append(OutcomeClass.POSSESSION_ORDER)

    for m in _CONDUCT.finditer(body):
        span = m.group(0).strip()
        obligations.append(
            Obligation(
                obligation_id=_oid(),
                kind=ObligationKind.CONDUCT,
                party="unknown",
                description=span,
                confidence=0.65,
                source_span=span[:200],
            )
        )
        if OutcomeClass.CONDUCT_ORDER not in classes:
            classes.append(OutcomeClass.CONDUCT_ORDER)

    if _DISMISS.search(body):
        if OutcomeClass.DISMISSAL not in classes:
            classes.append(OutcomeClass.DISMISSAL)
        obligations.append(
            Obligation(
                obligation_id=_oid(),
                kind=ObligationKind.DISMISSAL,
                party="both",
                description="Application dismissed (heuristic match).",
                confidence=0.8,
                source_span="dismissal",
            )
        )

    if not classes:
        classes = [OutcomeClass.UNKNOWN]
        notes.append("No outcome class matched — full human review required.")
    elif len(classes) > 1:
        classes = [OutcomeClass.MIXED] + [c for c in classes if c != OutcomeClass.MIXED]

    confs = [o.confidence for o in obligations] or [0.3]
    overall = min(confs) if obligations else 0.3
    hitl = overall < 0.85 or not obligations or OutcomeClass.UNKNOWN in classes

    return ParsedDecision(
        matter_id=matter_id,
        decision_date=decision_date,
        outcome_classes=classes,
        obligations=obligations,
        raw_excerpt=body[:2000],
        overall_confidence=overall,
        hitl_required=hitl,
        notes=notes,
    )
