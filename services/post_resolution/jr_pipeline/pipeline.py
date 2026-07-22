"""
Judicial review pipeline under post_resolution (Layer 6).

Error extraction: procedural fairness, patent unreasonableness, error of law, jurisdiction.
60-day clock is a placeholder — confirm JRPA / limitation with counsel.
Not legal advice.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class JrErrorGround(str, Enum):
    PROCEDURAL_FAIRNESS = "PROCEDURAL_FAIRNESS"
    PATENT_UNREASONABLENESS = "PATENT_UNREASONABLENESS"  # historic label; post-Vavilov: reasonableness
    REASONABLENESS = "REASONABLENESS"
    ERROR_OF_LAW = "ERROR_OF_LAW"
    JURISDICTION = "JURISDICTION"
    OTHER = "OTHER"


_GROUND_PATTERNS: list[tuple[JrErrorGround, re.Pattern[str]]] = [
    (JrErrorGround.PROCEDURAL_FAIRNESS, re.compile(
        r"no\s+opportunity\s+to\s+(?:respond|be\s+heard)|bias|notice\s+not|"
        r"procedural\s+fairness|audi\s+alteram", re.I)),
    (JrErrorGround.REASONABLENESS, re.compile(
        r"unreasonable|vavilov|patently\s+unreasonable|no\s+evidence|"
        r"ignored\s+evidence", re.I)),
    (JrErrorGround.ERROR_OF_LAW, re.compile(
        r"error\s+of\s+law|misinterpret(?:ed|ation)\s+(?:the\s+)?(?:act|rta|section)|"
        r"wrong\s+legal\s+test", re.I)),
    (JrErrorGround.JURISDICTION, re.compile(
        r"jurisdiction|ultra\s+vires|no\s+authority", re.I)),
]


@dataclass
class JrErrorFlag:
    ground: JrErrorGround
    description: str
    confidence: float = 0.6

    def to_dict(self) -> dict[str, Any]:
        return {
            "ground": self.ground.value,
            "description": self.description,
            "confidence": self.confidence,
        }


@dataclass
class JrClock:
    """
    Prefer services.deadlines.jr_clock.calculate_jr_clock for uncertainty modes.
    This thin clock assumes issuance date == decision_date when finality known.
    """

    matter_id: str
    decision_date: str  # issuance date of final decision when known
    window_days: int = 60
    petition_filed: bool = False
    clock_mode: str = "STANDARD_60_FROM_ISSUANCE"
    hitl_required: bool = True
    notes: str = (
        "Ordinary RTB JR pathway: 60 days from issuance of the final decision. "
        "Confirm finality, issuance date, JRPA/ATA on BC Laws. "
        "ATA s.57(2) extension is counsel-driven, not automatic."
    )

    def deadline(self) -> Optional[str]:
        try:
            d = date.fromisoformat(self.decision_date[:10])
        except ValueError:
            return None
        return (d + timedelta(days=self.window_days)).isoformat()

    def days_remaining(self, today: Optional[date] = None) -> Optional[int]:
        dl = self.deadline()
        if not dl:
            return None
        t = today or date.today()
        return (date.fromisoformat(dl) - t).days

    def to_dict(self) -> dict[str, Any]:
        from services.deadlines.jr_clock import JrClockRequest, calculate_jr_clock

        calc = calculate_jr_clock(
            JrClockRequest(
                matter_id=self.matter_id,
                issuance_date=self.decision_date,
                finality_known=True,
                enabling_act_known=True,
                human_confirmed=not self.hitl_required,
            )
        )
        return {
            "matter_id": self.matter_id,
            "decision_date": self.decision_date,
            "issuance_date": self.decision_date,
            "window_days": self.window_days,
            "deadline": self.deadline(),
            "days_remaining": self.days_remaining(),
            "petition_filed": self.petition_filed,
            "clock_mode": calc.clock_mode.value,
            "hitl_required": calc.hitl_required,
            "alternatives": calc.alternatives,
            "notes": self.notes,
            "form_for_petition": "Form 66",
            "form_for_response": "Form 67",
            "form_for_interlocutory": "Form 32",
        }


@dataclass
class PetitionScaffold:
    matter_id: str
    form_code: str = "Form 66"  # Rule 16-1: petition = Form 66; Form 67 = response
    grounds: list[str] = field(default_factory=list)
    relief_sought: list[str] = field(default_factory=list)
    status: str = "DRAFT"
    notes: str = (
        "Scaffold only — petition is Form 66 (not Form 67). "
        "Lawyer must settle grounds and authorities on BC Laws / CanLII."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "matter_id": self.matter_id,
            "form_code": self.form_code,
            "grounds": list(self.grounds),
            "relief_sought": list(self.relief_sought),
            "status": self.status,
            "notes": self.notes,
        }


@dataclass
class JrEvidenceBinder:
    matter_id: str
    tabs: list[dict[str, str]] = field(default_factory=list)
    notes: str = "JR-format binder index — map each item to EvidenceNode node_id."

    def to_dict(self) -> dict[str, Any]:
        return {
            "matter_id": self.matter_id,
            "tabs": list(self.tabs),
            "notes": self.notes,
        }


def extract_errors(text: str) -> list[JrErrorFlag]:
    flags: list[JrErrorFlag] = []
    for ground, pat in _GROUND_PATTERNS:
        m = pat.search(text or "")
        if m:
            flags.append(
                JrErrorFlag(
                    ground=ground,
                    description=m.group(0)[:200],
                    confidence=0.65,
                )
            )
    # Map patent unreasonableness language to reasonableness ground already
    if re.search(r"patently\s+unreasonable", text or "", re.I):
        if not any(f.ground == JrErrorGround.PATENT_UNREASONABLENESS for f in flags):
            flags.append(
                JrErrorFlag(
                    ground=JrErrorGround.PATENT_UNREASONABLENESS,
                    description="Historic 'patent unreasonableness' language detected — "
                    "frame under current Vavilov reasonableness framework with counsel.",
                    confidence=0.7,
                )
            )
    return flags


def default_binder(matter_id: str) -> JrEvidenceBinder:
    return JrEvidenceBinder(
        matter_id=matter_id,
        tabs=[
            {"tab": "1", "title": "Petition / style of cause"},
            {"tab": "2", "title": "Decision under review"},
            {"tab": "3", "title": "Record of proceedings (RTB file)"},
            {"tab": "4", "title": "Hearing audio / transcript excerpts"},
            {"tab": "5", "title": "Affidavits"},
            {"tab": "6", "title": "Authorities (BOA — BC Laws / CanLII)"},
            {"tab": "7", "title": "Draft order / stay materials"},
        ],
    )


@dataclass
class JrPipeline:
    clocks: dict[str, JrClock] = field(default_factory=dict)
    errors: dict[str, list[JrErrorFlag]] = field(default_factory=dict)
    petitions: dict[str, PetitionScaffold] = field(default_factory=dict)
    binders: dict[str, JrEvidenceBinder] = field(default_factory=dict)

    def detect_unfavorable(
        self,
        *,
        matter_id: str,
        client_role: str,  # tenant | landlord
        outcome_classes: list[str],
        possession_against_client: bool = False,
        monetary_against_client: bool = False,
    ) -> bool:
        if possession_against_client or monetary_against_client:
            return True
        # crude: dismissal of client's application
        if "DISMISSAL" in outcome_classes:
            return True
        if client_role == "tenant" and "POSSESSION_ORDER" in outcome_classes:
            return True
        return False

    def trigger(
        self,
        *,
        matter_id: str,
        decision_date: str,
        decision_or_notes_text: str = "",
        client_role: str = "tenant",
        outcome_classes: Optional[list[str]] = None,
        force: bool = False,
    ) -> dict[str, Any]:
        classes = outcome_classes or []
        unfavorable = force or self.detect_unfavorable(
            matter_id=matter_id,
            client_role=client_role,
            outcome_classes=classes,
            possession_against_client="POSSESSION_ORDER" in classes and client_role == "tenant",
        )
        clock = JrClock(matter_id=matter_id, decision_date=decision_date)
        self.clocks[matter_id] = clock
        flags = extract_errors(decision_or_notes_text)
        self.errors[matter_id] = flags
        petition = PetitionScaffold(
            matter_id=matter_id,
            grounds=[f.description for f in flags]
            or ["[Grounds to be settled by counsel — procedural fairness / reasonableness / law / jurisdiction]"],
            relief_sought=[
                "Order setting aside the decision",
                "Such further and other relief as this Honourable Court deems just",
            ],
        )
        self.petitions[matter_id] = petition
        binder = default_binder(matter_id)
        self.binders[matter_id] = binder
        return {
            "unfavorable_trigger": unfavorable,
            "clock": clock.to_dict(),
            "errors": [f.to_dict() for f in flags],
            "petition": petition.to_dict(),
            "evidence_binder": binder.to_dict(),
        }
