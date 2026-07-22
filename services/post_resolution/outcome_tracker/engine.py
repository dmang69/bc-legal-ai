"""
Outcome Tracking Engine — structured obligations + compliance clocks +
predicted vs actual comparison (feeds weakness / failure-mode analysis).

Not legal advice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from services.post_resolution.obligation_parser.parser import (
    Obligation,
    OutcomeClass,
    ParsedDecision,
    parse_decision_text,
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _add_days(iso_date: str, days: int) -> Optional[str]:
    try:
        d = date.fromisoformat(iso_date[:10])
    except ValueError:
        return None
    return (d + timedelta(days=days)).isoformat()


@dataclass
class ComplianceClock:
    clock_id: str
    obligation_id: str
    matter_id: str
    party: str
    label: str  # e.g. "Landlord must remediate within X days"
    start_date: Optional[str]
    due_date: Optional[str]
    status: str = "OPEN"  # OPEN | DONE | MISSED | WAIVED

    def to_dict(self) -> dict[str, Any]:
        return {
            "clock_id": self.clock_id,
            "obligation_id": self.obligation_id,
            "matter_id": self.matter_id,
            "party": self.party,
            "label": self.label,
            "start_date": self.start_date,
            "due_date": self.due_date,
            "status": self.status,
        }


@dataclass
class PredictedVsActual:
    matter_id: str
    predicted_summary: str
    actual_summary: str
    predicted_classes: list[str]
    actual_classes: list[str]
    match: bool
    delta_notes: list[str] = field(default_factory=list)
    # Feed to Weakness / Failure Mode Predictor
    failure_mode_tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "matter_id": self.matter_id,
            "predicted_summary": self.predicted_summary,
            "actual_summary": self.actual_summary,
            "predicted_classes": list(self.predicted_classes),
            "actual_classes": list(self.actual_classes),
            "match": self.match,
            "delta_notes": list(self.delta_notes),
            "failure_mode_tags": list(self.failure_mode_tags),
        }


@dataclass
class OutcomeTrackingRecord:
    matter_id: str
    decision_date: Optional[str]
    outcome_classes: list[str]
    obligations: list[Obligation]
    clocks: list[ComplianceClock]
    comparison: Optional[PredictedVsActual] = None
    ingested_at: str = field(default_factory=_utcnow)
    source: str = "text"  # text | pdf_ocr
    hitl_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "matter_id": self.matter_id,
            "decision_date": self.decision_date,
            "outcome_classes": list(self.outcome_classes),
            "obligations": [o.to_dict() for o in self.obligations],
            "clocks": [c.to_dict() for c in self.clocks],
            "comparison": self.comparison.to_dict() if self.comparison else None,
            "ingested_at": self.ingested_at,
            "source": self.source,
            "hitl_required": self.hitl_required,
        }


def _clock_label(obl: Obligation) -> str:
    if obl.kind.value == "REPAIR":
        if obl.deadline_days:
            return f"Landlord must remediate within {obl.deadline_days} days"
        if obl.deadline_date:
            return f"Landlord must remediate by {obl.deadline_date}"
        return "Landlord must remediate (deadline to confirm from order)"
    if obl.kind.value in ("VACATE", "POSSESSION"):
        if obl.deadline_date:
            return f"Tenant must vacate by {obl.deadline_date}"
        if obl.deadline_days:
            return f"Tenant must vacate within {obl.deadline_days} days of order"
        return "Tenant must vacate (confirm possession / vacate date on order)"
    if obl.kind.value == "MONETARY":
        amt = f"${obl.amount:,.2f}" if obl.amount is not None else "amount TBD"
        if obl.deadline_days:
            return f"{obl.party.title()} must pay {amt} within {obl.deadline_days} days"
        return f"{obl.party.title()} must pay {amt} (confirm due date on order)"
    return obl.description[:120]


def generate_clocks(
    matter_id: str,
    obligations: list[Obligation],
    decision_date: Optional[str],
) -> list[ComplianceClock]:
    clocks: list[ComplianceClock] = []
    for obl in obligations:
        if obl.kind.value == "DISMISSAL":
            continue
        due = obl.deadline_date
        if not due and obl.deadline_days and decision_date:
            due = _add_days(decision_date, obl.deadline_days)
        clocks.append(
            ComplianceClock(
                clock_id=f"CLK-{uuid4().hex[:10]}",
                obligation_id=obl.obligation_id,
                matter_id=matter_id,
                party=obl.party,
                label=_clock_label(obl),
                start_date=decision_date,
                due_date=due,
            )
        )
    return clocks


def compare_predicted_actual(
    matter_id: str,
    *,
    predicted_summary: str,
    predicted_classes: list[str],
    actual: ParsedDecision,
) -> PredictedVsActual:
    actual_classes = [c.value for c in actual.outcome_classes]
    pred_set = {c.upper() for c in predicted_classes}
    act_set = set(actual_classes)
    match = bool(pred_set) and pred_set == act_set
    notes: list[str] = []
    tags: list[str] = []
    if not predicted_classes:
        notes.append("No prediction recorded for comparison.")
        tags.append("NO_PREDICTION")
    elif not match:
        missing = act_set - pred_set
        extra = pred_set - act_set
        if missing:
            notes.append(f"Actual classes not predicted: {sorted(missing)}")
            tags.append("UNDER_PREDICTED")
        if extra:
            notes.append(f"Predicted classes not in actual: {sorted(extra)}")
            tags.append("OVER_PREDICTED")
        if OutcomeClass.DISMISSAL.value in act_set and OutcomeClass.DISMISSAL.value not in pred_set:
            tags.append("UNEXPECTED_DISMISSAL")
        if OutcomeClass.POSSESSION_ORDER.value in act_set:
            tags.append("POSSESSION_OUTCOME")
    actual_summary = "; ".join(o.description[:80] for o in actual.obligations[:5]) or (
        ", ".join(actual_classes)
    )
    return PredictedVsActual(
        matter_id=matter_id,
        predicted_summary=predicted_summary,
        actual_summary=actual_summary,
        predicted_classes=list(predicted_classes),
        actual_classes=actual_classes,
        match=match,
        delta_notes=notes,
        failure_mode_tags=tags,
    )


@dataclass
class OutcomeTracker:
    records: dict[str, OutcomeTrackingRecord] = field(default_factory=dict)
    predictions: dict[str, dict[str, Any]] = field(default_factory=dict)

    def set_prediction(
        self,
        matter_id: str,
        *,
        summary: str,
        classes: list[str],
    ) -> None:
        self.predictions[matter_id] = {"summary": summary, "classes": list(classes)}

    def ingest_decision_text(
        self,
        *,
        matter_id: str,
        text: str,
        decision_date: Optional[str] = None,
        source: str = "text",
    ) -> OutcomeTrackingRecord:
        parsed = parse_decision_text(
            text, matter_id=matter_id, decision_date=decision_date
        )
        clocks = generate_clocks(matter_id, parsed.obligations, parsed.decision_date)
        comparison = None
        pred = self.predictions.get(matter_id)
        if pred:
            comparison = compare_predicted_actual(
                matter_id,
                predicted_summary=pred["summary"],
                predicted_classes=pred["classes"],
                actual=parsed,
            )
        rec = OutcomeTrackingRecord(
            matter_id=matter_id,
            decision_date=parsed.decision_date,
            outcome_classes=[c.value for c in parsed.outcome_classes],
            obligations=list(parsed.obligations),
            clocks=clocks,
            comparison=comparison,
            source=source,
            hitl_required=parsed.hitl_required,
        )
        self.records[matter_id] = rec
        return rec

    def get(self, matter_id: str) -> Optional[OutcomeTrackingRecord]:
        return self.records.get(matter_id)
