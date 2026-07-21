"""
Examination / cross-examination outline contracts.

Drafting support for hearing prep — not legal advice.
Every question should cite a transcript timestamp and/or EvidenceNode.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class QuestionPurpose(str, Enum):
    FOUNDATIONAL = "foundational"
    LOCK_IN = "lock_in"
    CONFRONT = "confront"
    IMPEACH = "impeach"
    CREDIBILITY = "credibility"
    DOCUMENT = "document"
    PRIOR_INCONSISTENT = "prior_inconsistent"
    OTHER = "other"


@dataclass
class TranscriptPin:
    """Pinpoint into a hearing / discovery transcript."""

    timestamp: str  # e.g. "02:22" or "63:17"
    quote: Optional[str] = None
    source_label: str = "Transcript"
    evidence_node_id: Optional[str] = None  # if transcript is an EvidenceNode

    def format(self) -> str:
        base = f"{self.source_label} [{self.timestamp}]"
        if self.quote:
            return f'{base} — "{self.quote}"'
        return base

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "quote": self.quote,
            "source_label": self.source_label,
            "evidence_node_id": self.evidence_node_id,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "TranscriptPin":
        return TranscriptPin(
            timestamp=str(data.get("timestamp") or ""),
            quote=data.get("quote"),
            source_label=str(data.get("source_label") or "Transcript"),
            evidence_node_id=data.get("evidence_node_id"),
        )


@dataclass
class ExaminationQuestion:
    question_id: str
    text: str
    purpose: QuestionPurpose = QuestionPurpose.OTHER
    purpose_label: str = ""  # free-text e.g. "Foundational — establish her role"
    source_transcript: Optional[TranscriptPin] = None
    source_evidence_nodes: list[str] = field(default_factory=list)  # EM-019 / EV-…
    expected_answer: str = ""
    purpose_note: str = ""  # strategic purpose beyond expected answer
    follow_ups: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "text": self.text,
            "purpose": self.purpose.value,
            "purpose_label": self.purpose_label,
            "source_transcript": (
                self.source_transcript.to_dict() if self.source_transcript else None
            ),
            "source_evidence_nodes": list(self.source_evidence_nodes),
            "expected_answer": self.expected_answer,
            "purpose_note": self.purpose_note,
            "follow_ups": list(self.follow_ups),
            "tags": list(self.tags),
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ExaminationQuestion":
        pin = data.get("source_transcript")
        return ExaminationQuestion(
            question_id=str(data.get("question_id") or f"Q-{uuid4().hex[:6]}"),
            text=str(data.get("text") or ""),
            purpose=QuestionPurpose(data.get("purpose", QuestionPurpose.OTHER.value)),
            purpose_label=str(data.get("purpose_label") or ""),
            source_transcript=TranscriptPin.from_dict(pin) if pin else None,
            source_evidence_nodes=list(data.get("source_evidence_nodes") or []),
            expected_answer=str(data.get("expected_answer") or ""),
            purpose_note=str(data.get("purpose_note") or data.get("purpose") or ""),
            follow_ups=list(data.get("follow_ups") or []),
            tags=list(data.get("tags") or []),
        )

    def format_block(self) -> str:
        label = self.purpose_label or self.purpose.value
        lines = [
            f"{self.question_id}: [{label}]",
            f'  "{self.text}"',
        ]
        if self.source_transcript:
            lines.append(f"  Source: {self.source_transcript.format()}")
        if self.source_evidence_nodes:
            lines.append(
                f"  Source: Evidence node(s) {', '.join(self.source_evidence_nodes)}"
            )
        if self.expected_answer:
            lines.append(f"  Expected: {self.expected_answer}")
        if self.purpose_note:
            lines.append(f"  Purpose: {self.purpose_note}")
        for fu in self.follow_ups:
            lines.append(f"  Follow-up: {fu}")
        return "\n".join(lines)


@dataclass
class ExaminationOutline:
    """
    Cross-examination or examination-in-chief outline.

    Goal-driven; each question should be source-linked.
    """

    outline_id: str
    title: str
    target_witness: str
    goal: str
    exam_type: str = "CROSS"  # CROSS | CHIEF | RE_EXAM
    party_calling: str = ""
    questions: list[ExaminationQuestion] = field(default_factory=list)
    matter_id: Optional[str] = None
    related_legal_tests: list[str] = field(default_factory=list)
    notes: str = ""
    disclaimer: str = (
        "Examination outline for hearing preparation only. Not legal advice. "
        "Confirm transcript quotes against the official recording/transcript. "
        "Expected answers are planning assumptions, not guarantees."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "outline_id": self.outline_id,
            "title": self.title,
            "target_witness": self.target_witness,
            "goal": self.goal,
            "exam_type": self.exam_type,
            "party_calling": self.party_calling,
            "questions": [q.to_dict() for q in self.questions],
            "matter_id": self.matter_id,
            "related_legal_tests": list(self.related_legal_tests),
            "notes": self.notes,
            "disclaimer": self.disclaimer,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ExaminationOutline":
        return ExaminationOutline(
            outline_id=str(data.get("outline_id") or f"EXAM-{uuid4().hex[:8]}"),
            title=str(data.get("title") or ""),
            target_witness=str(data.get("target_witness") or ""),
            goal=str(data.get("goal") or ""),
            exam_type=str(data.get("exam_type") or "CROSS"),
            party_calling=str(data.get("party_calling") or ""),
            questions=[
                ExaminationQuestion.from_dict(q) for q in (data.get("questions") or [])
            ],
            matter_id=data.get("matter_id"),
            related_legal_tests=list(data.get("related_legal_tests") or []),
            notes=str(data.get("notes") or ""),
            disclaimer=str(
                data.get("disclaimer")
                or ExaminationOutline(
                    outline_id="", title="", target_witness="", goal=""
                ).disclaimer
            ),
        )

    def format_outline(self) -> str:
        lines = [
            f"EXAMINATION OUTLINE — {self.exam_type} OF {self.target_witness.upper()}",
            f"Target: {self.target_witness}",
            f"Goal: {self.goal}",
            "",
        ]
        for q in self.questions:
            lines.append(q.format_block())
            lines.append("")
        if self.notes:
            lines.append("Notes:")
            lines.append(self.notes)
            lines.append("")
        lines.append(f"> {self.disclaimer}")
        return "\n".join(lines).rstrip() + "\n"
