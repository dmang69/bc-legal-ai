"""
Judicial review limitation clock (ordinary RTB pathway).

Default: 60 days from issuance of the final decision.
When finality, issuance date, or enabling legislation is uncertain, emit
alternatives — never invent a definitive client-facing deadline.

ATA s.57(2) extension is a counsel pathway: track only, do not auto-grant.

Confirm JRPA / ATA / enabling Act on BC Laws before filing. Not legal advice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Any, Optional


class JrClockMode(str, Enum):
    STANDARD_60_FROM_ISSUANCE = "STANDARD_60_FROM_ISSUANCE"
    FINALITY_UNCERTAIN = "FINALITY_UNCERTAIN"
    ISSUANCE_UNKNOWN = "ISSUANCE_UNKNOWN"
    ENABLING_ACT_UNCERTAIN = "ENABLING_ACT_UNCERTAIN"
    ATA_S57_2_EXTENSION_PATH = "ATA_S57_2_EXTENSION_PATH"


@dataclass
class JrClockRequest:
    matter_id: str
    issuance_date: Optional[str] = None  # ISO date final decision issued
    finality_known: bool = True
    enabling_act_known: bool = True
    extension_sought: bool = False
    human_confirmed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "matter_id": self.matter_id,
            "issuance_date": self.issuance_date,
            "finality_known": self.finality_known,
            "enabling_act_known": self.enabling_act_known,
            "extension_sought": self.extension_sought,
            "human_confirmed": self.human_confirmed,
        }


@dataclass
class JrClockResult:
    matter_id: str
    clock_mode: JrClockMode
    primary_deadline: Optional[str]
    window_days: int = 60
    alternatives: list[dict[str, Any]] = field(default_factory=list)
    hitl_required: bool = True
    client_display: str = ""
    counsel_notes: list[str] = field(default_factory=list)
    statute_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "matter_id": self.matter_id,
            "clock_mode": self.clock_mode.value,
            "primary_deadline": self.primary_deadline,
            "window_days": self.window_days,
            "alternatives": list(self.alternatives),
            "hitl_required": self.hitl_required,
            "client_display": self.client_display,
            "counsel_notes": list(self.counsel_notes),
            "statute_refs": list(self.statute_refs),
            "deadline_status": "HUMAN_CONFIRMED"
            if not self.hitl_required
            else "CALCULATED_UNCONFIRMED",
        }


def _add_days(iso: str, days: int) -> Optional[str]:
    try:
        d = date.fromisoformat(iso[:10])
    except ValueError:
        return None
    return (d + timedelta(days=days)).isoformat()


def calculate_jr_clock(req: JrClockRequest) -> JrClockResult:
    """
    Ordinary RTB judicial-review clock: 60 days from issuance of final decision.

    ATA s.57(2): extension power exists under statutory criteria — human only.
    """
    refs = [
        "Administrative Tribunals Act (BC) s.57 — time limit / extension pathway (confirm current text on BC Laws)",
        "Judicial Review Procedure Act — procedure (confirm current text on BC Laws)",
    ]
    notes = [
        "Potential deadline only until supervising counsel confirms finality, issuance date, and enabling legislation.",
        "Do not present as definitive to the client without HUMAN_CONFIRMED.",
    ]

    if req.extension_sought:
        primary = None
        if req.issuance_date:
            primary = _add_days(req.issuance_date, 60)
        return JrClockResult(
            matter_id=req.matter_id,
            clock_mode=JrClockMode.ATA_S57_2_EXTENSION_PATH,
            primary_deadline=primary,
            alternatives=[
                {
                    "label": "Standard 60-day period from issuance (if no extension)",
                    "deadline": primary,
                },
                {
                    "label": "ATA s.57(2) extension application pathway",
                    "deadline": None,
                    "note": "Extension is discretionary under statutory criteria — counsel must apply; system does not grant extensions.",
                },
            ],
            hitl_required=True,
            client_display=(
                "A limitation period may apply. Counsel is assessing whether a standard "
                "60-day period or an extension pathway under the Administrative Tribunals Act applies."
            ),
            counsel_notes=notes
            + [
                "Track extension application deadlines and evidence of delay criteria separately.",
            ],
            statute_refs=refs,
        )

    if not req.issuance_date:
        return JrClockResult(
            matter_id=req.matter_id,
            clock_mode=JrClockMode.ISSUANCE_UNKNOWN,
            primary_deadline=None,
            alternatives=[
                {
                    "label": "Once issuance date of final decision is known",
                    "rule": "STANDARD_60_FROM_ISSUANCE",
                    "deadline": None,
                },
            ],
            hitl_required=True,
            client_display=(
                "Potential judicial-review deadline cannot be calculated yet — "
                "issuance date of the final decision is not confirmed."
            ),
            counsel_notes=notes + ["Obtain certified decision / issuance date."],
            statute_refs=refs,
        )

    primary = _add_days(req.issuance_date, 60)
    alternatives: list[dict[str, Any]] = []

    if not req.finality_known:
        alternatives.append(
            {
                "label": "If decision is final as issued",
                "deadline": primary,
                "mode": JrClockMode.STANDARD_60_FROM_ISSUANCE.value,
            }
        )
        alternatives.append(
            {
                "label": "If further tribunal steps remain (not final)",
                "deadline": None,
                "mode": JrClockMode.FINALITY_UNCERTAIN.value,
                "note": "Clock may not start until final decision issues.",
            }
        )
        return JrClockResult(
            matter_id=req.matter_id,
            clock_mode=JrClockMode.FINALITY_UNCERTAIN,
            primary_deadline=None,
            alternatives=alternatives,
            hitl_required=True,
            client_display=(
                "Potential judicial-review timelines depend on whether the decision is final. "
                "Counsel is reviewing."
            ),
            counsel_notes=notes,
            statute_refs=refs,
        )

    if not req.enabling_act_known:
        alternatives.append(
            {
                "label": "Ordinary ATA / RTB-linked 60-day assumption",
                "deadline": primary,
            }
        )
        alternatives.append(
            {
                "label": "Alternate enabling statute limitation (to be identified)",
                "deadline": None,
            }
        )
        return JrClockResult(
            matter_id=req.matter_id,
            clock_mode=JrClockMode.ENABLING_ACT_UNCERTAIN,
            primary_deadline=None,
            alternatives=alternatives,
            hitl_required=True,
            client_display=(
                "Potential deadline under review — enabling legislation is not yet confirmed."
            ),
            counsel_notes=notes + ["Confirm enabling Act and any special limitation."],
            statute_refs=refs,
        )

    hitl = not req.human_confirmed
    return JrClockResult(
        matter_id=req.matter_id,
        clock_mode=JrClockMode.STANDARD_60_FROM_ISSUANCE,
        primary_deadline=primary,
        alternatives=[
            {
                "label": "ATA s.57(2) extension pathway (if criteria met — counsel only)",
                "deadline": None,
            }
        ],
        hitl_required=hitl,
        client_display=(
            f"Calculated potential deadline {primary} (60 days from issuance {req.issuance_date[:10]}). "
            + (
                "Confirmed by counsel."
                if req.human_confirmed
                else "Not yet confirmed for client reliance."
            )
        ),
        counsel_notes=notes,
        statute_refs=refs,
    )
