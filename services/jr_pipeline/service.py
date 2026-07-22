"""
Appeal / JR preparation pipeline — trigger, error id, 60-day clock, petition scaffold.

Confirm limitation with counsel and JRPA. Not legal advice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Optional


@dataclass
class JrClock:
    matter_id: str
    decision_date: str  # ISO date
    window_days: int = 60  # placeholder — confirm with counsel
    petition_filed: bool = False
    notes: str = ""

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
        return {
            "matter_id": self.matter_id,
            "decision_date": self.decision_date,
            "window_days": self.window_days,
            "deadline": self.deadline(),
            "days_remaining": self.days_remaining(),
            "petition_filed": self.petition_filed,
            "notes": self.notes
            or "Confirm JRPA limitation and service rules with supervising counsel.",
        }


@dataclass
class JrErrorFlag:
    code: str
    description: str
    severity: str = "WARNING"

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "description": self.description,
            "severity": self.severity,
        }


@dataclass
class PetitionScaffold:
    matter_id: str
    form_code: str = "Form 66"  # Rule 16-1 petition; Form 67 is response
    grounds: list[str] = field(default_factory=list)
    relief_sought: list[str] = field(default_factory=list)
    status: str = "DRAFT"
    notes: str = "Scaffold only — Form 66 petition. Lawyer must settle grounds and authorities."

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
class JrPipelineStub:
    clocks: dict[str, JrClock] = field(default_factory=dict)
    errors: dict[str, list[JrErrorFlag]] = field(default_factory=dict)
    petitions: dict[str, PetitionScaffold] = field(default_factory=dict)

    def open_clock(self, clock: JrClock) -> JrClock:
        self.clocks[clock.matter_id] = clock
        return clock

    def trigger_jr(
        self,
        *,
        matter_id: str,
        decision_date: str,
        error_codes: Optional[list[tuple[str, str]]] = None,
    ) -> dict[str, Any]:
        clock = self.open_clock(JrClock(matter_id=matter_id, decision_date=decision_date))
        flags = [
            JrErrorFlag(code=c, description=d)
            for c, d in (error_codes or [])
        ]
        self.errors[matter_id] = flags
        petition = PetitionScaffold(
            matter_id=matter_id,
            grounds=[f.description for f in flags] or ["[Grounds to be settled by counsel]"],
            relief_sought=["Order setting aside the decision", "Such further relief as this Court deems just"],
        )
        self.petitions[matter_id] = petition
        return {
            "clock": clock.to_dict(),
            "errors": [f.to_dict() for f in flags],
            "petition": petition.to_dict(),
        }
