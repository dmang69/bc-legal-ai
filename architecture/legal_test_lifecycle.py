"""
LegalTest activation state machine (M0-012).

DRAFT → SOURCE_VERIFIED → LEGAL_REVIEW → APPROVED → ACTIVE → SUPERSEDED | DISABLED
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class LegalTestLifecycle(str, Enum):
    DRAFT = "DRAFT"
    SOURCE_VERIFIED = "SOURCE_VERIFIED"
    LEGAL_REVIEW = "LEGAL_REVIEW"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    DISABLED = "DISABLED"


ALLOWED_TRANSITIONS: dict[LegalTestLifecycle, set[LegalTestLifecycle]] = {
    LegalTestLifecycle.DRAFT: {
        LegalTestLifecycle.SOURCE_VERIFIED,
        LegalTestLifecycle.DISABLED,
    },
    LegalTestLifecycle.SOURCE_VERIFIED: {
        LegalTestLifecycle.LEGAL_REVIEW,
        LegalTestLifecycle.DISABLED,
    },
    LegalTestLifecycle.LEGAL_REVIEW: {
        LegalTestLifecycle.APPROVED,
        LegalTestLifecycle.DRAFT,
        LegalTestLifecycle.DISABLED,
    },
    LegalTestLifecycle.APPROVED: {
        LegalTestLifecycle.ACTIVE,
        LegalTestLifecycle.DISABLED,
    },
    LegalTestLifecycle.ACTIVE: {
        LegalTestLifecycle.SUPERSEDED,
        LegalTestLifecycle.DISABLED,
    },
    LegalTestLifecycle.SUPERSEDED: {LegalTestLifecycle.DISABLED},
    LegalTestLifecycle.DISABLED: set(),
}


@dataclass
class LifecycleRecord:
    test_id: str
    state: LegalTestLifecycle
    history: list[dict[str, Any]] = field(default_factory=list)

    def transition(
        self,
        new_state: LegalTestLifecycle,
        *,
        actor: str,
        note: str = "",
    ) -> None:
        if new_state not in ALLOWED_TRANSITIONS.get(self.state, set()):
            raise ValueError(
                f"Illegal transition {self.state.value} → {new_state.value} for {self.test_id}"
            )
        if new_state == LegalTestLifecycle.ACTIVE and not actor:
            raise ValueError("ACTIVE requires authenticated lawyer actor")
        self.history.append(
            {
                "from": self.state.value,
                "to": new_state.value,
                "actor": actor,
                "note": note,
            }
        )
        self.state = new_state

    def is_callable(self) -> bool:
        return self.state == LegalTestLifecycle.ACTIVE
