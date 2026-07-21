"""
Plain-language document explainer for tenants / SRLs.

WHAT THIS SAYS / MEANS / FINDINGS / ERRORS / OPTIONS structure.
Not legal advice — discussion aid for use with a lawyer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import uuid4


@dataclass
class ExplainerSection:
    heading: str
    bullets: list[str] = field(default_factory=list)
    body: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "heading": self.heading,
            "bullets": list(self.bullets),
            "body": self.body,
        }

    def format_block(self) -> str:
        lines = [f"{self.heading}:"]
        if self.body:
            lines.append(self.body)
        for b in self.bullets:
            lines.append(f"- {b}")
        return "\n".join(lines)


@dataclass
class DocumentExplainer:
    """
    Structured plain-language explanation of a legal document.
    """

    explainer_id: str = field(default_factory=lambda: f"EXP-{uuid4().hex[:8]}")
    document_title: str = ""
    document_date: Optional[str] = None
    document_revision: Optional[str] = None  # e.g. REV January 20
    matter_id: Optional[str] = None
    evidence_node_id: Optional[str] = None  # EM / EV when uploaded
    what_this_says: list[str] = field(default_factory=list)
    what_this_means: list[str] = field(default_factory=list)
    key_findings: list[str] = field(default_factory=list)
    possible_errors: list[str] = field(default_factory=list)
    options: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)
    placeholders_remaining: list[str] = field(default_factory=list)
    disclaimer: str = (
        "This explanation is not legal advice. It is a plain-language "
        "summary to help you understand the document and discuss it "
        "with a lawyer."
    )

    def document_line(self) -> str:
        line = f"DOCUMENT: {self.document_title}"
        if self.document_date:
            line += f" dated {self.document_date}"
        if self.document_revision:
            line += f" ({self.document_revision})"
        return line

    def to_dict(self) -> dict[str, Any]:
        return {
            "explainer_id": self.explainer_id,
            "document_title": self.document_title,
            "document_date": self.document_date,
            "document_revision": self.document_revision,
            "matter_id": self.matter_id,
            "evidence_node_id": self.evidence_node_id,
            "what_this_says": list(self.what_this_says),
            "what_this_means": list(self.what_this_means),
            "key_findings": list(self.key_findings),
            "possible_errors": list(self.possible_errors),
            "options": list(self.options),
            "resources": list(self.resources),
            "placeholders_remaining": list(self.placeholders_remaining),
            "disclaimer": self.disclaimer,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "DocumentExplainer":
        return DocumentExplainer(
            explainer_id=str(data.get("explainer_id") or f"EXP-{uuid4().hex[:8]}"),
            document_title=str(data.get("document_title") or ""),
            document_date=data.get("document_date"),
            document_revision=data.get("document_revision"),
            matter_id=data.get("matter_id"),
            evidence_node_id=data.get("evidence_node_id"),
            what_this_says=list(data.get("what_this_says") or []),
            what_this_means=list(data.get("what_this_means") or []),
            key_findings=list(data.get("key_findings") or []),
            possible_errors=list(data.get("possible_errors") or []),
            options=list(data.get("options") or []),
            resources=list(data.get("resources") or []),
            placeholders_remaining=list(data.get("placeholders_remaining") or []),
            disclaimer=str(
                data.get("disclaimer")
                or DocumentExplainer().disclaimer
            ),
        )

    def format_explainer(self) -> str:
        lines = [
            self.document_line(),
            "",
            "WHAT THIS SAYS:",
        ]
        for b in self.what_this_says:
            lines.append(f"- {b}")
        lines.append("")
        lines.append("WHAT THIS MEANS:")
        for b in self.what_this_means:
            lines.append(f"- {b}")
        lines.append("")
        lines.append("KEY FINDINGS THE ARBITRATOR MADE:")
        if self.key_findings:
            for b in self.key_findings:
                lines.append(f"- {b}")
        else:
            lines.append("- [Summarized in plain language — pending full decision text]")
        lines.append("")
        lines.append("WHERE THE ARBITRATOR MAY HAVE ERRED:")
        if self.possible_errors:
            for b in self.possible_errors:
                lines.append(f"- {b}")
        else:
            lines.append("- [Listed from petition / Layer 3 analysis when available]")
        lines.append("")
        lines.append("YOUR OPTIONS:")
        for b in self.options:
            lines.append(f"- {b}")
        if self.resources:
            lines.append("")
            lines.append("RESOURCES:")
            for r in self.resources:
                lines.append(f"- {r}")
        if self.placeholders_remaining:
            lines.append("")
            lines.append("PLACEHOLDERS TO COMPLETE WHEN DECISION ARRIVES:")
            for p in self.placeholders_remaining:
                lines.append(f"- {p}")
        lines.append("")
        lines.append(f"⚠ {self.disclaimer}")
        return "\n".join(lines)
