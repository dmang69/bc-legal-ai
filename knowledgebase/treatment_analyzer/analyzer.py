"""
Authority Treatment and Appellate History Analyzer.

Not a Shepard’s replacement. Human verifies any treatment used in a filing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class TreatmentSignal(str, Enum):
    APPEALED = "APPEALED"
    AFFIRMED = "AFFIRMED"
    REVERSED = "REVERSED"
    VARIED = "VARIED"
    DISTINGUISHED = "DISTINGUISHED"
    FOLLOWED = "FOLLOWED"
    QUESTIONED = "QUESTIONED"
    CRITICIZED = "CRITICIZED"
    LEGISLATIVE_OVERRIDE = "LEGISLATIVE_OVERRIDE"
    SUPERSEDED_STATUTORY_CONTEXT = "SUPERSEDED_STATUTORY_CONTEXT"
    UNKNOWN = "UNKNOWN"


@dataclass
class TreatmentResult:
    authority_id: str
    signals: list[TreatmentSignal]
    notes: str
    human_verification_required: bool = True
    status: str = "TREATMENT_REVIEWED_PENDING_HUMAN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_id": self.authority_id,
            "signals": [s.value for s in self.signals],
            "notes": self.notes,
            "human_verification_required": self.human_verification_required,
            "status": self.status,
        }


@dataclass
class AuthorityTreatmentAnalyzer:
    """Scaffold — no live citator. Records UNKNOWN until human/API fills."""

    cache: dict[str, TreatmentResult] = field(default_factory=dict)

    def analyze(self, authority_id: str, hints: Optional[list[str]] = None) -> TreatmentResult:
        if authority_id in self.cache:
            return self.cache[authority_id]
        signals: list[TreatmentSignal] = []
        for h in hints or []:
            hu = h.upper()
            for sig in TreatmentSignal:
                if sig.value in hu or sig.name in hu:
                    signals.append(sig)
        if not signals:
            signals = [TreatmentSignal.UNKNOWN]
        result = TreatmentResult(
            authority_id=authority_id,
            signals=signals,
            notes=(
                "Authority Treatment and Appellate History Analyzer (scaffold). "
                "Confirm on CanLII / official reporter before court-ready use."
            ),
        )
        self.cache[authority_id] = result
        return result
