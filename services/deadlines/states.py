"""
Deadline verification states (M0-E3).

Only HUMAN_CONFIRMED may be presented as definitive to clients.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class DeadlineState(str, Enum):
    UNASSESSED = "UNASSESSED"
    POTENTIAL = "POTENTIAL"
    CALCULATED = "CALCULATED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    HUMAN_CONFIRMED = "HUMAN_CONFIRMED"
    DISPUTED = "DISPUTED"
    EXPIRED = "EXPIRED"
    EXTENSION_ANALYSIS_REQUIRED = "EXTENSION_ANALYSIS_REQUIRED"


@dataclass
class DeadlineResult:
    matter_id: str
    label: str
    state: DeadlineState
    due_date: Optional[str] = None
    assumptions: list[str] = field(default_factory=list)
    missing_inputs: list[str] = field(default_factory=list)
    statutory_basis: str = ""
    synthetic: bool = False
    client_display: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "matter_id": self.matter_id,
            "label": self.label,
            "state": self.state.value,
            "due_date": self.due_date,
            "assumptions": list(self.assumptions),
            "missing_inputs": list(self.missing_inputs),
            "statutory_basis": self.statutory_basis,
            "synthetic": self.synthetic,
            "client_display": self.client_display,
            "definitive_for_client": self.state == DeadlineState.HUMAN_CONFIRMED,
        }


def calculate_deadline(
    *,
    matter_id: str,
    label: str,
    start_date: Optional[str] = None,
    service_method: Optional[str] = None,
    window_days: Optional[int] = None,
    human_confirmed: bool = False,
    synthetic: bool = False,
    statutory_basis: str = "",
) -> DeadlineResult:
    """
    Fail-closed provisional interface (M0-015).
    Full holiday/service engine is M5 — this never invents certainty.
    """
    missing: list[str] = []
    if not start_date:
        missing.append("start_date")
    if not service_method:
        missing.append("service_method")
    if window_days is None:
        missing.append("window_days")

    if missing:
        return DeadlineResult(
            matter_id=matter_id,
            label=label,
            state=DeadlineState.HUMAN_REVIEW_REQUIRED,
            missing_inputs=missing,
            statutory_basis=statutory_basis,
            synthetic=synthetic,
            client_display=(
                "Potential deadline cannot be calculated — missing inputs: "
                + ", ".join(missing)
                + ". Counsel review required."
            ),
        )

    from datetime import date, timedelta

    try:
        d = date.fromisoformat(start_date[:10])
    except ValueError:
        return DeadlineResult(
            matter_id=matter_id,
            label=label,
            state=DeadlineState.HUMAN_REVIEW_REQUIRED,
            missing_inputs=["start_date_invalid"],
            synthetic=synthetic,
            client_display="Start date invalid. Human review required.",
        )

    # Provisional calendar-day add only — not holiday/deemed-service aware
    due = (d + timedelta(days=int(window_days))).isoformat()
    assumptions = [
        f"calendar days (+{window_days}) without holiday adjustment",
        f"service_method={service_method} not yet applied for deemed receipt",
    ]
    state = (
        DeadlineState.HUMAN_CONFIRMED
        if human_confirmed
        else DeadlineState.CALCULATED
    )
    if not human_confirmed:
        state = DeadlineState.HUMAN_REVIEW_REQUIRED

    return DeadlineResult(
        matter_id=matter_id,
        label=label,
        state=state,
        due_date=due,
        assumptions=assumptions,
        statutory_basis=statutory_basis,
        synthetic=synthetic,
        client_display=(
            f"Deadline {due} is HUMAN_CONFIRMED."
            if human_confirmed
            else f"Calculated potential date {due} — not definitive until counsel confirms "
            f"(service method, holidays, finality)."
        ),
    )
