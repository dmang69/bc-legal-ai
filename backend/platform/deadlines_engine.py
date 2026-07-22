"""
Deadline calculation facade (M5 start) — wraps provisional states + JR clock.
Only HUMAN_CONFIRMED is definitive for client display.
"""

from __future__ import annotations

from typing import Any, Optional

from services.deadlines.jr_clock import JrClockRequest, calculate_jr_clock
from services.deadlines.states import DeadlineResult, DeadlineState, calculate_deadline


def calculate_matter_deadline(
    *,
    matter_id: str,
    label: str,
    start_date: Optional[str] = None,
    service_method: Optional[str] = None,
    window_days: Optional[int] = None,
    human_confirmed: bool = False,
    synthetic: bool = True,
    statutory_basis: str = "",
) -> dict[str, Any]:
    r: DeadlineResult = calculate_deadline(
        matter_id=matter_id,
        label=label,
        start_date=start_date,
        service_method=service_method,
        window_days=window_days,
        human_confirmed=human_confirmed,
        synthetic=synthetic,
        statutory_basis=statutory_basis,
    )
    return r.to_dict()


def calculate_jr(
    *,
    matter_id: str,
    issuance_date: Optional[str] = None,
    finality_known: bool = True,
    enabling_act_known: bool = True,
    extension_sought: bool = False,
    human_confirmed: bool = False,
) -> dict[str, Any]:
    return calculate_jr_clock(
        JrClockRequest(
            matter_id=matter_id,
            issuance_date=issuance_date,
            finality_known=finality_known,
            enabling_act_known=enabling_act_known,
            extension_sought=extension_sought,
            human_confirmed=human_confirmed,
        )
    )


def is_definitive(state: str) -> bool:
    return state == DeadlineState.HUMAN_CONFIRMED.value
