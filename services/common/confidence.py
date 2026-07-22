"""
Confidence scoring + HITL fallback (Layer 1 / reasoning shared).

Fail-closed: low confidence routes to human review, never silent acceptance.
Not legal advice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class HitlReason(str, Enum):
    LOW_CLASSIFICATION = "LOW_CLASSIFICATION"
    LOW_EXTRACTION = "LOW_EXTRACTION"
    LOW_TRANSCRIPTION = "LOW_TRANSCRIPTION"
    NEAR_DUPLICATE = "NEAR_DUPLICATE"
    PRIVILEGE_SIGNAL = "PRIVILEGE_SIGNAL"
    CONTRADICTION = "CONTRADICTION"
    UNSUPPORTED_LEGAL_TEST = "UNSUPPORTED_LEGAL_TEST"
    CONFLICTED_LEGAL_TEST = "CONFLICTED_LEGAL_TEST"
    HALLUCINATION_ATTEMPT = "HALLUCINATION_ATTEMPT"
    MISSING_METADATA = "MISSING_METADATA"
    MANUAL_FLAG = "MANUAL_FLAG"


# Default thresholds (tunable per env)
CLASSIFY_HITL = 0.75
EXTRACT_HITL = 0.70
TRANSCRIBE_HITL = 0.80


@dataclass
class ConfidenceScore:
    classification: float = 0.0
    extraction: float = 0.0
    transcription: Optional[float] = None
    overall: float = 0.0
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "classification": self.classification,
            "extraction": self.extraction,
            "transcription": self.transcription,
            "overall": self.overall,
            "notes": list(self.notes),
        }


@dataclass
class HitlDecision:
    required: bool
    reasons: list[HitlReason] = field(default_factory=list)
    severity: str = "info"  # info | warn | critical
    auto_escalate: bool = False
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "required": self.required,
            "reasons": [r.value for r in self.reasons],
            "severity": self.severity,
            "auto_escalate": self.auto_escalate,
            "message": self.message,
        }


def score_confidence(
    *,
    classification: float,
    extraction: float,
    transcription: Optional[float] = None,
    privilege_signal: bool = False,
    near_duplicate: bool = False,
    missing_metadata: bool = False,
) -> tuple[ConfidenceScore, HitlDecision]:
    """
    Compute overall confidence and whether HITL is required.

    Overall = min of available channel scores (fail-closed min).
    """
    channels = [classification, extraction]
    if transcription is not None:
        channels.append(transcription)
    overall = min(channels) if channels else 0.0
    score = ConfidenceScore(
        classification=max(0.0, min(1.0, classification)),
        extraction=max(0.0, min(1.0, extraction)),
        transcription=None
        if transcription is None
        else max(0.0, min(1.0, transcription)),
        overall=max(0.0, min(1.0, overall)),
    )
    reasons: list[HitlReason] = []
    if classification < CLASSIFY_HITL:
        reasons.append(HitlReason.LOW_CLASSIFICATION)
        score.notes.append(f"classification {classification:.2f} < {CLASSIFY_HITL}")
    if extraction < EXTRACT_HITL:
        reasons.append(HitlReason.LOW_EXTRACTION)
        score.notes.append(f"extraction {extraction:.2f} < {EXTRACT_HITL}")
    if transcription is not None and transcription < TRANSCRIBE_HITL:
        reasons.append(HitlReason.LOW_TRANSCRIPTION)
        score.notes.append(f"transcription {transcription:.2f} < {TRANSCRIBE_HITL}")
    if privilege_signal:
        reasons.append(HitlReason.PRIVILEGE_SIGNAL)
    if near_duplicate:
        reasons.append(HitlReason.NEAR_DUPLICATE)
    if missing_metadata:
        reasons.append(HitlReason.MISSING_METADATA)

    severity = "info"
    auto_escalate = False
    if HitlReason.PRIVILEGE_SIGNAL in reasons:
        severity = "critical"
        auto_escalate = True
    elif reasons:
        severity = "warn"

    required = bool(reasons)
    msg = (
        "Human-in-the-loop review required before evidence node finalization."
        if required
        else "Auto-path allowed subject to privilege and grounding gates."
    )
    return score, HitlDecision(
        required=required,
        reasons=reasons,
        severity=severity,
        auto_escalate=auto_escalate,
        message=msg,
    )
