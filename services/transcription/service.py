"""
Audio/video handler skeleton — transcription + diarization.

Production: wire Whisper/faster-whisper + pyannote (or cloud STT) behind
private infra. Public Spaces must not receive unredacted hearing audio.

Not legal advice. Transcripts require human verification before quoting in filings.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DiarizedSegment:
    start_sec: float
    end_sec: float
    speaker: str
    text: str
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "start_sec": self.start_sec,
            "end_sec": self.end_sec,
            "speaker": self.speaker,
            "text": self.text,
            "confidence": self.confidence,
        }


@dataclass
class TranscriptionResult:
    media_hash: str
    language: str = "en"
    full_text: str = ""
    segments: list[DiarizedSegment] = field(default_factory=list)
    diarization_available: bool = False
    confidence: float = 0.0
    engine: str = "stub"
    hitl_required: bool = True
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "media_hash": self.media_hash,
            "language": self.language,
            "full_text": self.full_text,
            "segments": [s.to_dict() for s in self.segments],
            "diarization_available": self.diarization_available,
            "confidence": self.confidence,
            "engine": self.engine,
            "hitl_required": self.hitl_required,
            "notes": list(self.notes),
        }


def transcribe_audio_stub(
    data: bytes,
    *,
    filename: str = "",
    language: str = "en",
    enable_diarization: bool = True,
) -> TranscriptionResult:
    """
    Placeholder: does not run a model. Marks HITL required always.

    When a real engine is wired, replace this body; keep HITL on low confidence.
    """
    digest = hashlib.sha256(data).hexdigest()
    notes = [
        "STUB: no model weights loaded — transcription not performed.",
        "Queue for human transcription or private GPU STT job.",
        f"filename={filename or 'unknown'}",
    ]
    segments: list[DiarizedSegment] = []
    if enable_diarization:
        notes.append("Diarization placeholder reserved (SPEAKER_00 / SPEAKER_01).")
    return TranscriptionResult(
        media_hash=f"sha256:{digest}",
        language=language,
        full_text="",
        segments=segments,
        diarization_available=False,
        confidence=0.0,
        engine="stub",
        hitl_required=True,
        notes=notes,
    )
