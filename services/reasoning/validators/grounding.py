"""Validators for reasoning outputs (skeleton)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    ok: bool
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"ok": self.ok, "issues": list(self.issues)}


_CITE_HINT = re.compile(r"\b(s\.?\s*\d+|section\s+\d+|RTA|JRPA|Vavilov)\b", re.I)


def validate_no_unverified_citations(
    text: str,
    *,
    verified_pins: set[str] | None = None,
) -> ValidationResult:
    """
    Fail-closed heuristic: any section-like cite without a verified pin is flagged.
    Production: integrate backend.grounding.GroundingGate.
    """
    verified_pins = verified_pins or set()
    issues: list[str] = []
    for m in _CITE_HINT.finditer(text or ""):
        pin = m.group(0)
        # Allow only if exact pin is in verified set (caller supplies)
        if pin not in verified_pins and not any(pin in v for v in verified_pins):
            issues.append(f"UNVERIFIED_CITATION_FLAG: {pin}")
    return ValidationResult(ok=not issues, issues=issues)
