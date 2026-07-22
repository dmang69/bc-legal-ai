"""
Document classification microservice (rule-based skeleton).

Labels: court filing, RTB decision, email, photo, audio, etc.
Production: replace heuristics with supervised model behind HITL thresholds.
Not legal advice.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from architecture.evidence_node import SourceType


class DocumentClass(str, Enum):
    COURT_FILING = "COURT_FILING"
    RTB_DECISION = "RTB_DECISION"
    COURT_ORDER = "COURT_ORDER"
    EMAIL = "EMAIL"
    PHOTO = "PHOTO"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    LEASE = "LEASE"
    NOTICE = "NOTICE"
    FINANCIAL = "FINANCIAL"
    MEDICAL = "MEDICAL"
    GOVERNMENT_LETTER = "GOVERNMENT_LETTER"
    WITNESS_STATEMENT = "WITNESS_STATEMENT"
    TEXT_MESSAGE = "TEXT_MESSAGE"
    OTHER = "OTHER"


# Map classifier label → EvidenceNode SourceType
CLASS_TO_SOURCE: dict[DocumentClass, SourceType] = {
    DocumentClass.COURT_FILING: SourceType.OTHER,  # extend SourceType later if needed
    DocumentClass.RTB_DECISION: SourceType.RTB_DECISION,
    DocumentClass.COURT_ORDER: SourceType.COURT_ORDER,
    DocumentClass.EMAIL: SourceType.EMAIL,
    DocumentClass.PHOTO: SourceType.PHOTO,
    DocumentClass.AUDIO: SourceType.AUDIO_RECORDING,
    DocumentClass.VIDEO: SourceType.VIDEO,
    DocumentClass.LEASE: SourceType.LEASE_AGREEMENT,
    DocumentClass.NOTICE: SourceType.GOVERNMENT_CORRESPONDENCE,
    DocumentClass.FINANCIAL: SourceType.BANK_RECORD,
    DocumentClass.MEDICAL: SourceType.MEDICAL_RECORD,
    DocumentClass.GOVERNMENT_LETTER: SourceType.GOVERNMENT_CORRESPONDENCE,
    DocumentClass.WITNESS_STATEMENT: SourceType.WITNESS_STATEMENT,
    DocumentClass.TEXT_MESSAGE: SourceType.TEXT_MESSAGE,
    DocumentClass.OTHER: SourceType.OTHER,
}


_RULES: list[tuple[DocumentClass, list[str], float]] = [
    (DocumentClass.RTB_DECISION, [r"\bresidential tenancy branch\b", r"\bartbitrator\b", r"\brtb\b.*\bdecision\b"], 0.9),
    (DocumentClass.COURT_ORDER, [r"\border of\b", r"\bsupreme court of british columbia\b", r"\bmaster\b.*\border\b"], 0.85),
    (DocumentClass.COURT_FILING, [r"\bpetition\b", r"\baffidavit\b", r"\bnotice of application\b", r"\bform 66\b", r"\bform 67\b"], 0.85),
    (DocumentClass.EMAIL, [r"^from:\s", r"^subject:\s", r"\b@\w+\.\w+", r"\bmessage-id\b"], 0.8),
    (DocumentClass.LEASE, [r"\btenancy agreement\b", r"\blease\b", r"\brent\s*\$"], 0.8),
    (DocumentClass.NOTICE, [r"\bten day notice\b", r"\bone month notice\b", r"\btwo month notice\b", r"\bfour month notice\b", r"\brt[b]?-"], 0.85),
    (DocumentClass.MEDICAL, [r"\bmedical\b", r"\bphysician\b", r"\bdiagnosis\b", r"\bphn\b"], 0.75),
    (DocumentClass.FINANCIAL, [r"\breceipt\b", r"\binvoice\b", r"\be-?transfer\b", r"\bbank statement\b"], 0.75),
    (DocumentClass.WITNESS_STATEMENT, [r"\bsworn\b", r"\baffirm\b", r"\bi witnessed\b"], 0.7),
    (DocumentClass.TEXT_MESSAGE, [r"\bsms\b", r"\bimessage\b", r"\bwhatsapp\b"], 0.7),
    (DocumentClass.GOVERNMENT_LETTER, [r"\bgovernment of british columbia\b", r"\bgov\.bc\.ca\b"], 0.75),
]


@dataclass
class ClassificationResult:
    label: DocumentClass
    confidence: float
    source_type: SourceType
    signals: list[str] = field(default_factory=list)
    hitl_recommended: bool = False

    def to_dict(self) -> dict:
        return {
            "label": self.label.value,
            "confidence": self.confidence,
            "source_type": self.source_type.value,
            "signals": list(self.signals),
            "hitl_recommended": self.hitl_recommended,
        }


def classify_document(
    *,
    filename: str = "",
    text: str = "",
    mime_hint: Optional[str] = None,
) -> ClassificationResult:
    """Rule-based classifier. Empty input → OTHER @ low confidence → HITL."""
    name = Path(filename or "").name.lower()
    body = (text or "").lower()
    combined = f"{name}\n{body}"
    mime = (mime_hint or "").lower()

    # Binary type shortcuts
    if any(name.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".heic", ".webp", ".gif", ".tif", ".tiff")):
        return ClassificationResult(
            label=DocumentClass.PHOTO,
            confidence=0.95,
            source_type=SourceType.PHOTO,
            signals=["extension:image"],
        )
    if any(name.endswith(ext) for ext in (".mp3", ".wav", ".m4a", ".ogg", ".flac")):
        return ClassificationResult(
            label=DocumentClass.AUDIO,
            confidence=0.95,
            source_type=SourceType.AUDIO_RECORDING,
            signals=["extension:audio"],
        )
    if any(name.endswith(ext) for ext in (".mp4", ".mov", ".webm", ".mkv")):
        return ClassificationResult(
            label=DocumentClass.VIDEO,
            confidence=0.95,
            source_type=SourceType.VIDEO,
            signals=["extension:video"],
        )
    if "image/" in mime:
        return ClassificationResult(
            label=DocumentClass.PHOTO, confidence=0.9, source_type=SourceType.PHOTO, signals=["mime:image"]
        )
    if "audio/" in mime:
        return ClassificationResult(
            label=DocumentClass.AUDIO,
            confidence=0.9,
            source_type=SourceType.AUDIO_RECORDING,
            signals=["mime:audio"],
        )
    if "video/" in mime:
        return ClassificationResult(
            label=DocumentClass.VIDEO, confidence=0.9, source_type=SourceType.VIDEO, signals=["mime:video"]
        )

    best: Optional[ClassificationResult] = None
    for label, patterns, base_conf in _RULES:
        hits = [p for p in patterns if re.search(p, combined, re.I | re.M)]
        if hits:
            conf = min(0.99, base_conf + 0.02 * (len(hits) - 1))
            cand = ClassificationResult(
                label=label,
                confidence=conf,
                source_type=CLASS_TO_SOURCE[label],
                signals=hits[:5],
                hitl_recommended=conf < 0.75,
            )
            if best is None or cand.confidence > best.confidence:
                best = cand

    if best is None:
        return ClassificationResult(
            label=DocumentClass.OTHER,
            confidence=0.35,
            source_type=SourceType.OTHER,
            signals=["no_rule_match"],
            hitl_recommended=True,
        )
    best.hitl_recommended = best.confidence < 0.75
    return best
