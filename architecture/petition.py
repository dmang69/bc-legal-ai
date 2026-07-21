"""
Petition / judicial review outline contracts.

Drafting support for JR petitions — not legal advice.
Every sub-ground should cite evidence (EM/EV nodes, transcript) and/or authorities.
Authorities must still pass GroundingGate / CitationDB for court-ready use.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class JRStandardLabel(str, Enum):
    """Label as pleaded — confirm current standard of review before filing."""

    PATENT_UNREASONABLENESS = "Patent Unreasonableness"
    REASONABLENESS = "Reasonableness"
    CORRECTNESS = "Correctness"
    PROCEDURAL_FAIRNESS = "Procedural Fairness"
    JURISDICTION = "Jurisdiction"
    OTHER = "Other"


@dataclass
class PetitionCite:
    """Evidence or transcript support for a sub-ground."""

    kind: str  # evidence | transcript | note | authority
    label: str
    detail: str = ""
    evidence_node_id: Optional[str] = None
    transcript_start: Optional[str] = None
    transcript_end: Optional[str] = None
    citation_short: Optional[str] = None
    verification_status: str = "UNVERIFIED"  # until CitationDB / record check

    def format_line(self) -> str:
        if self.kind == "transcript" and self.transcript_start:
            span = self.transcript_start
            if self.transcript_end:
                span = f"{self.transcript_start}-{self.transcript_end}"
            base = f"[Cite: Transcript {span}"
            if self.detail:
                base += f" — {self.detail}"
            return base + "]"
        if self.kind == "evidence":
            nid = self.evidence_node_id or self.label
            extra = f" — {self.detail}" if self.detail else ""
            return f"[Cite: {nid}{extra}]"
        if self.kind == "authority":
            cite = self.citation_short or self.label
            return f"[Legal authority: {cite}]"
        if self.kind == "note":
            return f"[Note: {self.detail or self.label}]"
        return f"[{self.label}]"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "label": self.label,
            "detail": self.detail,
            "evidence_node_id": self.evidence_node_id,
            "transcript_start": self.transcript_start,
            "transcript_end": self.transcript_end,
            "citation_short": self.citation_short,
            "verification_status": self.verification_status,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "PetitionCite":
        return PetitionCite(
            kind=str(data.get("kind") or "note"),
            label=str(data.get("label") or ""),
            detail=str(data.get("detail") or ""),
            evidence_node_id=data.get("evidence_node_id"),
            transcript_start=data.get("transcript_start"),
            transcript_end=data.get("transcript_end"),
            citation_short=data.get("citation_short"),
            verification_status=str(data.get("verification_status") or "UNVERIFIED"),
        )


@dataclass
class PetitionSubGround:
    sub_id: str  # e.g. 1a, 2b
    description: str
    cites: list[PetitionCite] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "sub_id": self.sub_id,
            "description": self.description,
            "cites": [c.to_dict() for c in self.cites],
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "PetitionSubGround":
        return PetitionSubGround(
            sub_id=str(data.get("sub_id") or ""),
            description=str(data.get("description") or ""),
            cites=[PetitionCite.from_dict(c) for c in (data.get("cites") or [])],
            notes=str(data.get("notes") or ""),
        )

    def format_block(self, indent: str = "  ") -> str:
        lines = [f"{indent}├─ {self.sub_id}: {self.description}"]
        for c in self.cites:
            lines.append(f"{indent}│       {c.format_line()}")
        if self.notes:
            lines.append(f"{indent}│       [Note: {self.notes}]")
        return "\n".join(lines)


@dataclass
class PetitionGround:
    ground_id: str  # e.g. GROUND 1
    title: str
    standard: JRStandardLabel = JRStandardLabel.OTHER
    sub_grounds: list[PetitionSubGround] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ground_id": self.ground_id,
            "title": self.title,
            "standard": self.standard.value,
            "sub_grounds": [s.to_dict() for s in self.sub_grounds],
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "PetitionGround":
        std = data.get("standard", JRStandardLabel.OTHER.value)
        return PetitionGround(
            ground_id=str(data.get("ground_id") or ""),
            title=str(data.get("title") or ""),
            standard=(
                JRStandardLabel(std)
                if not isinstance(std, JRStandardLabel)
                else std
            ),
            sub_grounds=[
                PetitionSubGround.from_dict(s) for s in (data.get("sub_grounds") or [])
            ],
        )

    def format_block(self) -> str:
        lines = [f"  GROUND {self.ground_id}: {self.title}"]
        n = len(self.sub_grounds)
        for i, sg in enumerate(self.sub_grounds):
            is_last = i == n - 1
            # rebuild connector for last child
            block = sg.format_block(indent="  ")
            if is_last:
                block = block.replace("├─", "└─", 1)
            lines.append(block)
            if not is_last:
                lines.append("  │")
        return "\n".join(lines)


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    MODERATE_HIGH = "MODERATE-HIGH"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class PredictedOpposition:
    """
    Devil's Advocate block against a petition ground.

    Planning tool for reply strategy — not a prediction of judicial outcome.
    """

    against_ground_id: str  # e.g. "1"
    against_title: str  # e.g. "Patent Unreasonableness"
    arguments: list[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.MODERATE
    risk_note: str = ""
    reply_hooks: list[str] = field(default_factory=list)  # optional counter-prep

    def to_dict(self) -> dict[str, Any]:
        return {
            "against_ground_id": self.against_ground_id,
            "against_title": self.against_title,
            "arguments": list(self.arguments),
            "risk_level": self.risk_level.value,
            "risk_note": self.risk_note,
            "reply_hooks": list(self.reply_hooks),
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "PredictedOpposition":
        rl = data.get("risk_level", RiskLevel.MODERATE.value)
        return PredictedOpposition(
            against_ground_id=str(data.get("against_ground_id") or ""),
            against_title=str(data.get("against_title") or ""),
            arguments=list(data.get("arguments") or []),
            risk_level=RiskLevel(rl) if not isinstance(rl, RiskLevel) else rl,
            risk_note=str(data.get("risk_note") or ""),
            reply_hooks=list(data.get("reply_hooks") or []),
        )

    def format_block(self) -> str:
        lines = [
            f"  AGAINST GROUND {self.against_ground_id} ({self.against_title}):",
        ]
        for a in self.arguments:
            lines.append(f"  - {a}")
        risk_line = f"  RISK LEVEL: {self.risk_level.value}"
        if self.risk_note:
            risk_line += f" — {self.risk_note}"
        lines.append(risk_line)
        if self.reply_hooks:
            lines.append("  Reply prep:")
            for h in self.reply_hooks:
                lines.append(f"    • {h}")
        return "\n".join(lines)


@dataclass
class PetitionOutline:
    """Judicial review / petition structure for drafting."""

    outline_id: str
    title: str = "PETITION OUTLINE"
    matter_id: Optional[str] = None
    court: str = "BC Supreme Court"
    statute_route: str = "Judicial Review Procedure Act"
    grounds: list[PetitionGround] = field(default_factory=list)
    predicted_opposition: list[PredictedOpposition] = field(default_factory=list)
    related_legal_tests: list[str] = field(default_factory=list)
    notes: str = ""
    disclaimer: str = (
        "Petition outline for drafting support only. Not legal advice. "
        "Confirm standard of review (Vavilov / statutory language), all transcript "
        "pins, and every authority on BC Laws / CanLII before filing. "
        "UNVERIFIED authorities must not appear in court-ready drafts without GroundingGate clearance. "
        "Predicted opposition is adversarial planning, not a forecast of court outcome."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "outline_id": self.outline_id,
            "title": self.title,
            "matter_id": self.matter_id,
            "court": self.court,
            "statute_route": self.statute_route,
            "grounds": [g.to_dict() for g in self.grounds],
            "predicted_opposition": [p.to_dict() for p in self.predicted_opposition],
            "related_legal_tests": list(self.related_legal_tests),
            "notes": self.notes,
            "disclaimer": self.disclaimer,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "PetitionOutline":
        return PetitionOutline(
            outline_id=str(data.get("outline_id") or f"PET-{uuid4().hex[:8]}"),
            title=str(data.get("title") or "PETITION OUTLINE"),
            matter_id=data.get("matter_id"),
            court=str(data.get("court") or "BC Supreme Court"),
            statute_route=str(
                data.get("statute_route") or "Judicial Review Procedure Act"
            ),
            grounds=[
                PetitionGround.from_dict(g) for g in (data.get("grounds") or [])
            ],
            predicted_opposition=[
                PredictedOpposition.from_dict(p)
                for p in (data.get("predicted_opposition") or [])
            ],
            related_legal_tests=list(data.get("related_legal_tests") or []),
            notes=str(data.get("notes") or ""),
            disclaimer=str(
                data.get("disclaimer")
                or PetitionOutline(outline_id="").disclaimer
            ),
        )

    def format_outline(self) -> str:
        lines = [f"{self.title}:", ""]
        for g in self.grounds:
            lines.append(g.format_block())
            lines.append("")
        if self.predicted_opposition:
            lines.append("PREDICTED OPPOSITION ARGUMENTS:")
            lines.append("")
            for p in self.predicted_opposition:
                lines.append(p.format_block())
                lines.append("")
        if self.notes:
            lines.append("Notes:")
            lines.append(self.notes)
            lines.append("")
        lines.append(f"> {self.disclaimer}")
        return "\n".join(lines).rstrip() + "\n"

    def format_opposition_only(self) -> str:
        lines = ["PREDICTED OPPOSITION ARGUMENTS:", ""]
        for p in self.predicted_opposition:
            lines.append(p.format_block())
            lines.append("")
        lines.append(
            "> Adversarial planning only — not a prediction of judicial outcome. Not legal advice."
        )
        return "\n".join(lines).rstrip() + "\n"

    def all_authority_cites(self) -> list[PetitionCite]:
        out: list[PetitionCite] = []
        for g in self.grounds:
            for s in g.sub_grounds:
                for c in s.cites:
                    if c.kind == "authority":
                        out.append(c)
        return out

    def all_evidence_ids(self) -> list[str]:
        ids: list[str] = []
        for g in self.grounds:
            for s in g.sub_grounds:
                for c in s.cites:
                    if c.evidence_node_id:
                        ids.append(c.evidence_node_id)
                    elif c.kind == "evidence" and c.label:
                        ids.append(c.label.split()[0])
        return ids
