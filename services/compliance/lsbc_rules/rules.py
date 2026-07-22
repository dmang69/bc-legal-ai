"""
LSBC-oriented record-keeping scaffolding.

These are **illustrative firm-facing defaults**, not official Law Society of BC
rules text. Confirm current LSBC Code, practice manuals, and firm policy before
reliance. Not legal advice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LsbcRetentionRules:
    """Minimum retention periods (years after matter close) — set firm policy."""

    min_evidence_years: int = 7
    min_privileged_years: int = 10
    min_client_comms_years: int = 7
    min_drafts_years: int = 3
    min_audit_years: int = 10
    privilege_handling: str = (
        "Privileged materials remain client-owned; production only via waiver / "
        "court order / production gate; never auto-produce."
    )
    conflict_retention_exception: str = (
        "Where conflict checks or multi-matter risk require longer retention of "
        "identity/conflict data, do not destroy until conflict system allows."
    )
    notes: str = (
        "Confirm with current LSBC requirements and firm file-retention policy. "
        "Do not treat these integers as legal minimums without counsel review."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "min_evidence_years": self.min_evidence_years,
            "min_privileged_years": self.min_privileged_years,
            "min_client_comms_years": self.min_client_comms_years,
            "min_drafts_years": self.min_drafts_years,
            "min_audit_years": self.min_audit_years,
            "privilege_handling": self.privilege_handling,
            "conflict_retention_exception": self.conflict_retention_exception,
            "notes": self.notes,
        }


def default_lsbc_rules() -> LsbcRetentionRules:
    return LsbcRetentionRules()


@dataclass
class MatterClosureRequirements:
    require_final_summary: bool = True
    require_retention_plan: bool = True
    require_privilege_lock: bool = True
    require_access_freeze: bool = True
    require_client_notification: bool = True


@dataclass
class ClosureValidation:
    ok: bool
    missing: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "missing": list(self.missing)}


def validate_closure(
    *,
    final_summary: str,
    retention_plan: Optional[list] = None,
    privilege_lock: bool = False,
    access_frozen: bool = False,
    client_notified: bool = False,
    requirements: Optional[MatterClosureRequirements] = None,
) -> ClosureValidation:
    req = requirements or MatterClosureRequirements()
    missing: list[str] = []
    if req.require_final_summary and not (final_summary or "").strip():
        missing.append("final_summary")
    if req.require_retention_plan and not retention_plan:
        missing.append("retention_plan")
    if req.require_privilege_lock and not privilege_lock:
        missing.append("privilege_lock")
    if req.require_access_freeze and not access_frozen:
        missing.append("access_freeze")
    if req.require_client_notification and not client_notified:
        missing.append("client_notification")
    return ClosureValidation(ok=not missing, missing=missing)
