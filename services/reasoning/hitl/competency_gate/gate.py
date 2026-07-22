"""
Competency gate — licensing, practice fit, currency (RTA/Rules/forms separate), conflict.

No emergency override bypasses privilege or conflict controls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from services.reasoning.hitl.competency_gate.profile import LawyerProfile


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# Task type → required practice areas + procedural permissions
TASK_REQUIREMENTS: dict[str, dict[str, list[str]]] = {
    "RTB_HEARING_SUBMISSION": {
        "areas": ["RESIDENTIAL_TENANCY"],
        "procedures": ["RTB"],
    },
    "JUDICIAL_REVIEW_PETITION": {
        "areas": ["ADMINISTRATIVE_LAW", "JUDICIAL_REVIEW"],
        "procedures": ["BC_SUPREME_COURT"],
    },
    "MEDICAL_CAUSATION_MEMO": {
        "areas": ["CIVIL_LITIGATION"],
        "procedures": [],
    },
    "PUBLIC_REGULATORY_RELEASE": {
        "areas": ["PRIVACY_REGULATORY"],
        "procedures": [],
    },
}


@dataclass
class CompetencyDecision:
    allowed: bool
    reasons: list[str] = field(default_factory=list)
    requires_override: bool = False
    override_token: Optional[str] = None
    backup_reviewer_suggested: Optional[str] = None
    practice_fit_recorded: bool = False
    conflict_clearance_current: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reasons": list(self.reasons),
            "requires_override": self.requires_override,
            "override_token": self.override_token,
            "backup_reviewer_suggested": self.backup_reviewer_suggested,
            "practice_fit_recorded": self.practice_fit_recorded,
            "conflict_clearance_current": self.conflict_clearance_current,
        }


@dataclass
class CompetencyGate:
    currency_max_days: int = 180

    def evaluate(
        self,
        lawyer: LawyerProfile,
        *,
        matter_id: str,
        required_areas: Optional[list[str]] = None,
        required_jurisdiction: str = "BC",
        task_type: Optional[str] = None,
        override: bool = False,
        override_reason: str = "",
        override_by_backup: bool = False,
        backup_reviewer: Optional[LawyerProfile] = None,
        supervising_authority_id: Optional[str] = None,
        required_currency_subjects: Optional[list[str]] = None,
    ) -> CompetencyDecision:
        reasons: list[str] = []
        areas = list(required_areas or [])
        procedures: list[str] = []
        if task_type and task_type in TASK_REQUIREMENTS:
            areas = list(TASK_REQUIREMENTS[task_type]["areas"])
            procedures = list(TASK_REQUIREMENTS[task_type]["procedures"])

        # normalize area names
        areas = [a.upper().replace(" ", "_") for a in areas]
        lawyer_areas = [a.upper().replace(" ", "_") for a in lawyer.practice_areas]

        if required_jurisdiction not in lawyer.licensing_jurisdictions:
            reasons.append(
                f"Jurisdiction {required_jurisdiction} not listed — BC licence required."
            )
        if lawyer.licence_status != "ACTIVE" and lawyer.bar_status != "active":
            reasons.append(f"Licence status is {lawyer.licence_status}, not ACTIVE.")

        for area in areas:
            if area not in lawyer_areas and area.lower() not in [
                x.lower() for x in lawyer.practice_areas
            ]:
                reasons.append(f"Practice area gap: {area} (RTB ≠ corporate).")
            if area in ("RESIDENTIAL_TENANCY", "JUDICIAL_REVIEW") and "CORPORATE" in lawyer_areas and area not in lawyer_areas:
                reasons.append(f"Incompatible practice mix for required {area}.")

        for proc in procedures:
            if proc not in lawyer.procedural_permissions:
                reasons.append(f"Procedural permission missing: {proc}")

        # Conflict — AI may flag; human determines disqualification
        conflict_ok = (
            lawyer.conflict_status == "CLEAR"
            or matter_id in lawyer.conflict_cleared_matters
        )
        if lawyer.conflict_status == "CONFIRMED_CONFLICT":
            reasons.append("Confirmed conflict — no emergency override of conflict controls.")
            conflict_ok = False
        elif not conflict_ok:
            reasons.append("Conflict check not recorded as CLEAR for this matter.")

        # Currency subjects versioned independently
        subjects = required_currency_subjects or ["RTA amendments"]
        if task_type == "RTB_HEARING_SUBMISSION":
            subjects = ["RTA amendments", "RTB Rules of Procedure", "RTB forms"]
        if task_type == "JUDICIAL_REVIEW_PETITION":
            subjects = ["JRPA", "Supreme Court Civil Rules", "Form 66"]

        for subj in subjects:
            rec = next(
                (c for c in lawyer.currency_records if subj.lower() in c.subject.lower()),
                None,
            )
            if not rec and lawyer.statute_currency_ack and "RTA" in subj:
                rec = type("R", (), {"verified_at": lawyer.statute_currency_ack})()
            if not rec:
                reasons.append(f"Currency not acknowledged: {subj}")
                continue
            try:
                ack = date.fromisoformat(str(rec.verified_at)[:10])
                if (date.today() - ack).days > self.currency_max_days:
                    reasons.append(
                        f"Currency ack for {subj} older than {self.currency_max_days} days."
                    )
            except ValueError:
                reasons.append(f"Invalid currency date for {subj}")

        practice_fit = not any("Practice area gap" in r for r in reasons)

        if not reasons:
            return CompetencyDecision(
                allowed=True,
                reasons=["Competency checks passed."],
                practice_fit_recorded=True,
                conflict_clearance_current=True,
            )

        backup_id = (
            (backup_reviewer.lawyer_id if backup_reviewer else None)
            or lawyer.backup_reviewer_id
        )

        if override:
            # Cannot override confirmed conflict or privilege (privilege is separate)
            if lawyer.conflict_status == "CONFIRMED_CONFLICT":
                return CompetencyDecision(
                    allowed=False,
                    reasons=reasons + ["Override cannot bypass confirmed conflict."],
                    requires_override=True,
                    backup_reviewer_suggested=backup_id,
                )
            if not override_reason.strip():
                return CompetencyDecision(
                    allowed=False,
                    reasons=reasons + ["Override requires a written reason."],
                    requires_override=True,
                    backup_reviewer_suggested=backup_id,
                )
            if override_by_backup and not backup_id:
                return CompetencyDecision(
                    allowed=False,
                    reasons=reasons + ["Backup reviewer required for override protocol."],
                    requires_override=True,
                )
            if override_by_backup and not supervising_authority_id:
                return CompetencyDecision(
                    allowed=False,
                    reasons=reasons
                    + ["Supervising authority must approve reassignment."],
                    requires_override=True,
                    backup_reviewer_suggested=backup_id,
                )
            token = f"OVR-{uuid4().hex[:8]}"
            return CompetencyDecision(
                allowed=True,
                reasons=reasons
                + [
                    f"Override accepted: {override_reason}",
                    f"decision_maker={supervising_authority_id or 'documented'}",
                    f"at {_utcnow()}",
                ],
                requires_override=True,
                override_token=token,
                backup_reviewer_suggested=backup_id,
                practice_fit_recorded=practice_fit,
                conflict_clearance_current=conflict_ok,
            )

        return CompetencyDecision(
            allowed=False,
            reasons=reasons,
            requires_override=True,
            backup_reviewer_suggested=backup_id,
            practice_fit_recorded=practice_fit,
            conflict_clearance_current=conflict_ok,
        )
