"""Pre-output privileged-material scan + waiver-risk heuristics."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional


_PRIV_PATTERNS = [
    r"\bprivileged\b",
    r"\bsolicitor[-\s–]client\b",
    r"\bwithout prejudice\b",
    r"\blegal advice\b",
    r"\bconfidential.*counsel\b",
    r"\battorney[-\s]client\b",
]

_WAIVER_RISK = [
    r"\bforward(?:ed)? to (?:landlord|opposing|tribunal|rtb)\b",
    r"\bcc:?\s*.*landlord",
    r"\bi waive\b",
    r"\bproduce to opposing\b",
]


@dataclass
class PrivilegePreservationResult:
    clean: bool
    hits: list[str] = field(default_factory=list)
    waiver_risks: list[str] = field(default_factory=list)
    two_factor_required: bool = False
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "clean": self.clean,
            "hits": list(self.hits),
            "waiver_risks": list(self.waiver_risks),
            "two_factor_required": self.two_factor_required,
            "message": self.message,
        }


def scan_pre_output(
    text: str,
    *,
    lawyer_confirmed: bool = False,
    second_factor_token: Optional[str] = None,
) -> PrivilegePreservationResult:
    hits = [p for p in _PRIV_PATTERNS if re.search(p, text or "", re.I)]
    risks = [p for p in _WAIVER_RISK if re.search(p, text or "", re.I)]
    if not hits and not risks:
        return PrivilegePreservationResult(
            clean=True,
            message="No privilege markers detected (heuristic — human review still required).",
        )
    two_factor_ok = bool(lawyer_confirmed and second_factor_token)
    if two_factor_ok:
        return PrivilegePreservationResult(
            clean=True,
            hits=hits,
            waiver_risks=risks,
            two_factor_required=True,
            message="Two-factor confirmation recorded; proceed with caution.",
        )
    return PrivilegePreservationResult(
        clean=False,
        hits=hits,
        waiver_risks=risks,
        two_factor_required=True,
        message="Blocked: privilege/waiver signals present. Require lawyer two-factor confirmation.",
    )
