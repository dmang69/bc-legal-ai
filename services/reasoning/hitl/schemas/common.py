"""Shared HITL decision types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ModelDestination(str, Enum):
    NONE = "NONE"
    PRIVATE_INFERENCE_ONLY = "PRIVATE_INFERENCE_ONLY"
    EXTERNAL_MODEL = "EXTERNAL_MODEL"
    PUBLIC_DEMO_FORBIDDEN = "PUBLIC_DEMO_FORBIDDEN"


class ProcessingBasis(str, Enum):
    CONSENT = "CONSENT"
    LEGAL_OBLIGATION = "LEGAL_OBLIGATION"
    LEGITIMATE_INTEREST_REVIEW = "LEGITIMATE_INTEREST_REVIEW"
    PROCESSING_PERMITTED_WITHOUT_CONSENT = "PROCESSING_PERMITTED_WITHOUT_CONSENT"
    NONE = "NONE"


@dataclass
class OperationDecision:
    permitted: bool
    basis: ProcessingBasis
    reasons: list[str] = field(default_factory=list)
    required_consents: list[str] = field(default_factory=list)
    privilege_review_required: bool = False
    freeze_export: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "permitted": self.permitted,
            "basis": self.basis.value,
            "reasons": list(self.reasons),
            "required_consents": list(self.required_consents),
            "privilege_review_required": self.privilege_review_required,
            "freeze_export": self.freeze_export,
            "metadata": dict(self.metadata),
        }


class ConsentGateBlocked(Exception):
    def __init__(self, reasons: list[str]):
        self.reasons = reasons
        super().__init__("; ".join(reasons))
