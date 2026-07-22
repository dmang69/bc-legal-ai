"""
Draft stay application scaffolding — serious question / irreparable harm / balance.

Not legal advice. Confirm SCR and authorities with counsel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StayApplicationScaffold:
    stay_id: str
    matter_id: str
    serious_question: str
    irreparable_harm: str
    balance_of_convenience: str
    draft_order_terms: list[str]
    status: str = "DRAFT"
    created_at: str = field(default_factory=_utcnow)
    notes: str = (
        "Three-part test scaffold only. Supporting affidavit and authorities required. "
        "Human lawyer must settle."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "stay_id": self.stay_id,
            "matter_id": self.matter_id,
            "serious_question": self.serious_question,
            "irreparable_harm": self.irreparable_harm,
            "balance_of_convenience": self.balance_of_convenience,
            "draft_order_terms": list(self.draft_order_terms),
            "status": self.status,
            "created_at": self.created_at,
            "notes": self.notes,
        }


@dataclass
class StayGenerator:
    stays: list[StayApplicationScaffold] = field(default_factory=list)

    def generate(
        self,
        matter_id: str,
        *,
        serious_question: str = "",
        irreparable_harm: str = "",
        balance_of_convenience: str = "",
        vacate_date: str = "",
    ) -> StayApplicationScaffold:
        stay = StayApplicationScaffold(
            stay_id=f"STAY-{uuid4().hex[:10]}",
            matter_id=matter_id,
            serious_question=serious_question
            or "[Serious question to be tried — e.g. procedural fairness / reasonableness grounds in petition]",
            irreparable_harm=irreparable_harm
            or (
                f"[Irreparable harm — e.g. loss of home if vacate by {vacate_date or 'order date'}; "
                "damages inadequate]"
            ),
            balance_of_convenience=balance_of_convenience
            or "[Balance of convenience — prejudice to each party; status quo; public interest]",
            draft_order_terms=[
                "The operation of the decision under review is stayed pending determination of the petition, "
                "or until further order of this Court.",
                "Costs in the cause / reserved.",
            ],
        )
        self.stays.append(stay)
        return stay
