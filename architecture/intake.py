"""
Tenancy dispute intake schema — structured matter opening.

Legal information capture for workbench matters. Not legal advice.
Deadlines are calculated from rules-based inputs; re-verify RTB rules before reliance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class NoticeType(str, Enum):
    TEN_DAY = "ten_day"  # unpaid rent/utilities
    ONE_MONTH = "one_month"  # cause
    TWO_MONTH = "two_month"  # landlord use
    FOUR_MONTH = "four_month"  # demolition/renovation/conversion
    OTHER = "other"
    UNKNOWN = "unknown"


class ServiceMethod(str, Enum):
    PERSONAL = "personal"
    POSTED = "posted"
    MAILED = "mailed"
    EMAIL = "email"
    OTHER = "other"
    UNKNOWN = "unknown"


class IssueCategory(str, Enum):
    HABITABILITY = "habitability"
    REPAIRS = "repairs"
    HARASSMENT = "harassment"
    RENT = "rent"
    RETALIATORY_EVICTION = "retaliatory_eviction"
    DEPOSIT = "deposit"
    ENTRY = "entry"
    OTHER = "other"


class DisabilityStatus(str, Enum):
    YES = "yes"
    NO = "no"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"
    UNKNOWN = "unknown"


@dataclass
class NoticeIntake:
    received: bool = False
    date_received: Optional[str] = None  # YYYY-MM-DD
    method: ServiceMethod = ServiceMethod.UNKNOWN
    notice_type: NoticeType = NoticeType.UNKNOWN
    notice_type_label: str = ""  # free text if OTHER
    upload_paths: list[str] = field(default_factory=list)  # relative evidence paths / node ids
    dispute_filed: Optional[bool] = None
    dispute_filed_date: Optional[str] = None
    dispute_file_number: Optional[str] = None
    # Calculated
    dispute_deadline: Optional[str] = None
    dispute_deadline_note: str = ""
    days_to_dispute: Optional[int] = None  # calendar days from service (rule of thumb)

    def to_dict(self) -> dict[str, Any]:
        return {
            "received": self.received,
            "date_received": self.date_received,
            "method": self.method.value,
            "notice_type": self.notice_type.value,
            "notice_type_label": self.notice_type_label,
            "upload_paths": list(self.upload_paths),
            "dispute_filed": self.dispute_filed,
            "dispute_filed_date": self.dispute_filed_date,
            "dispute_file_number": self.dispute_file_number,
            "dispute_deadline": self.dispute_deadline,
            "dispute_deadline_note": self.dispute_deadline_note,
            "days_to_dispute": self.days_to_dispute,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "NoticeIntake":
        return NoticeIntake(
            received=bool(data.get("received", False)),
            date_received=data.get("date_received"),
            method=ServiceMethod(data.get("method", ServiceMethod.UNKNOWN.value)),
            notice_type=NoticeType(data.get("notice_type", NoticeType.UNKNOWN.value)),
            notice_type_label=str(data.get("notice_type_label") or ""),
            upload_paths=list(data.get("upload_paths") or []),
            dispute_filed=data.get("dispute_filed"),
            dispute_filed_date=data.get("dispute_filed_date"),
            dispute_file_number=data.get("dispute_file_number"),
            dispute_deadline=data.get("dispute_deadline"),
            dispute_deadline_note=str(data.get("dispute_deadline_note") or ""),
            days_to_dispute=data.get("days_to_dispute"),
        )


@dataclass
class PriorProceeding:
    description: str = ""
    file_number: Optional[str] = None
    decision_date: Optional[str] = None
    upload_paths: list[str] = field(default_factory=list)
    complied_with: Optional[bool] = None
    compliance_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "file_number": self.file_number,
            "decision_date": self.decision_date,
            "upload_paths": list(self.upload_paths),
            "complied_with": self.complied_with,
            "compliance_notes": self.compliance_notes,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "PriorProceeding":
        return PriorProceeding(
            description=str(data.get("description") or ""),
            file_number=data.get("file_number"),
            decision_date=data.get("decision_date"),
            upload_paths=list(data.get("upload_paths") or []),
            complied_with=data.get("complied_with"),
            compliance_notes=str(data.get("compliance_notes") or ""),
        )


@dataclass
class CurrentIssue:
    categories: list[IssueCategory] = field(default_factory=list)
    category_other: str = ""
    timeline_start: Optional[str] = None
    ongoing: bool = True
    narrative: str = ""
    evidence_paths: list[str] = field(default_factory=list)
    landlord_notified: Optional[bool] = None
    landlord_notified_how: str = ""
    landlord_notified_when: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "categories": [c.value for c in self.categories],
            "category_other": self.category_other,
            "timeline_start": self.timeline_start,
            "ongoing": self.ongoing,
            "narrative": self.narrative,
            "evidence_paths": list(self.evidence_paths),
            "landlord_notified": self.landlord_notified,
            "landlord_notified_how": self.landlord_notified_how,
            "landlord_notified_when": self.landlord_notified_when,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "CurrentIssue":
        cats = []
        for c in data.get("categories") or []:
            try:
                cats.append(IssueCategory(c))
            except ValueError:
                cats.append(IssueCategory.OTHER)
        return CurrentIssue(
            categories=cats,
            category_other=str(data.get("category_other") or ""),
            timeline_start=data.get("timeline_start"),
            ongoing=bool(data.get("ongoing", True)),
            narrative=str(data.get("narrative") or ""),
            evidence_paths=list(data.get("evidence_paths") or []),
            landlord_notified=data.get("landlord_notified"),
            landlord_notified_how=str(data.get("landlord_notified_how") or ""),
            landlord_notified_when=data.get("landlord_notified_when"),
        )


@dataclass
class PersonalCircumstances:
    disability_status: DisabilityStatus = DisabilityStatus.UNKNOWN
    disability_notes: str = ""  # relevant for hardship — sensitive
    income_source: str = ""
    dependents: str = ""  # count or description
    housing_market_notes: str = ""  # vacancy, comparable rents
    consent_to_store_sensitive: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "disability_status": self.disability_status.value,
            "disability_notes": self.disability_notes
            if self.consent_to_store_sensitive
            else "",
            "income_source": self.income_source,
            "dependents": self.dependents,
            "housing_market_notes": self.housing_market_notes,
            "consent_to_store_sensitive": self.consent_to_store_sensitive,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "PersonalCircumstances":
        return PersonalCircumstances(
            disability_status=DisabilityStatus(
                data.get("disability_status", DisabilityStatus.UNKNOWN.value)
            ),
            disability_notes=str(data.get("disability_notes") or ""),
            income_source=str(data.get("income_source") or ""),
            dependents=str(data.get("dependents") or ""),
            housing_market_notes=str(data.get("housing_market_notes") or ""),
            consent_to_store_sensitive=bool(data.get("consent_to_store_sensitive", False)),
        )


@dataclass
class TenancyIntake:
    """
    INTAKE: Tenancy Dispute — full structured tree.
    """

    intake_id: str = field(default_factory=lambda: f"INTAKE-{uuid4().hex[:10]}")
    matter_id: Optional[str] = None
    # Property / tenancy
    property_address: str = ""
    unit_designation: str = ""  # e.g. 990, 990A
    tenancy_start_date: Optional[str] = None
    current_rent: Optional[str] = None  # keep as string for $ formatting
    lease_names: list[str] = field(default_factory=list)
    # Branches
    notice: NoticeIntake = field(default_factory=NoticeIntake)
    prior_proceedings: list[PriorProceeding] = field(default_factory=list)
    current_issues: CurrentIssue = field(default_factory=CurrentIssue)
    personal: PersonalCircumstances = field(default_factory=PersonalCircumstances)
    # Meta
    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )
    updated_at: str = ""
    incomplete_fields: list[str] = field(default_factory=list)
    disclaimer: str = (
        "Intake for workbench matter opening only. Not legal advice. "
        "Dispute deadlines are rule-of-thumb from notice type — confirm on RTB / RTA "
        "and account for deemed service before relying. Sensitive personal data requires consent."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "intake_id": self.intake_id,
            "matter_id": self.matter_id,
            "property_address": self.property_address,
            "unit_designation": self.unit_designation,
            "tenancy_start_date": self.tenancy_start_date,
            "current_rent": self.current_rent,
            "lease_names": list(self.lease_names),
            "notice": self.notice.to_dict(),
            "prior_proceedings": [p.to_dict() for p in self.prior_proceedings],
            "current_issues": self.current_issues.to_dict(),
            "personal": self.personal.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "incomplete_fields": list(self.incomplete_fields),
            "disclaimer": self.disclaimer,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "TenancyIntake":
        return TenancyIntake(
            intake_id=str(data.get("intake_id") or f"INTAKE-{uuid4().hex[:10]}"),
            matter_id=data.get("matter_id"),
            property_address=str(data.get("property_address") or ""),
            unit_designation=str(data.get("unit_designation") or ""),
            tenancy_start_date=data.get("tenancy_start_date"),
            current_rent=data.get("current_rent"),
            lease_names=list(data.get("lease_names") or []),
            notice=NoticeIntake.from_dict(data.get("notice") or {}),
            prior_proceedings=[
                PriorProceeding.from_dict(p)
                for p in (data.get("prior_proceedings") or [])
            ],
            current_issues=CurrentIssue.from_dict(data.get("current_issues") or {}),
            personal=PersonalCircumstances.from_dict(data.get("personal") or {}),
            created_at=str(data.get("created_at") or ""),
            updated_at=str(data.get("updated_at") or ""),
            incomplete_fields=list(data.get("incomplete_fields") or []),
            disclaimer=str(
                data.get("disclaimer")
                or TenancyIntake().disclaimer
            ),
        )

    def format_tree(self) -> str:
        """Human-readable intake tree for review."""
        n = self.notice
        lines = [
            "INTAKE: Tenancy Dispute",
            f"├─ Property address: {self.property_address or '(missing)'}",
            f"├─ Unit designation: {self.unit_designation or '(missing)'}",
            f"├─ Tenancy start date: {self.tenancy_start_date or '(missing)'}",
            f"├─ Current rent: {self.current_rent or '(missing)'}",
            f"├─ Who's on the lease: {', '.join(self.lease_names) or '(missing)'}",
            f"├─ Notice received: {'Yes' if n.received else 'No' if n.received is False else '(unknown)'}",
        ]
        if n.received:
            lines.append(f"│  ├─ Date received: {n.date_received or '(missing)'}")
            lines.append(f"│  ├─ Method: {n.method.value}")
            lines.append(
                f"│  ├─ Type: {n.notice_type.value}"
                + (f" ({n.notice_type_label})" if n.notice_type_label else "")
            )
            lines.append(
                f"│  ├─ Upload: {', '.join(n.upload_paths) or '(none yet)'}"
            )
            if n.dispute_filed:
                lines.append(
                    f"│  └─ Dispute filed: Yes — {n.dispute_filed_date or '?'} "
                    f"#{n.dispute_file_number or '?'}"
                )
            elif n.dispute_filed is False:
                lines.append(
                    f"│  └─ Dispute filed: No — deadline: "
                    f"{n.dispute_deadline or '(cannot calculate)'} "
                    f"{n.dispute_deadline_note}"
                )
            else:
                lines.append("│  └─ Dispute filed: (unknown)")
        lines.append(
            f"├─ Previous RTB proceedings: {len(self.prior_proceedings)} recorded"
        )
        for i, p in enumerate(self.prior_proceedings):
            mark = "└─" if i == len(self.prior_proceedings) - 1 else "├─"
            lines.append(
                f"│  {mark} {p.description or p.file_number or 'proceeding'} "
                f"(complied: {p.complied_with})"
            )
        cats = ", ".join(c.value for c in self.current_issues.categories) or "(none)"
        lines.append(f"├─ Current issues: {cats}")
        lines.append(
            f"│  ├─ Timeline start: {self.current_issues.timeline_start or '?'} "
            f"ongoing={self.current_issues.ongoing}"
        )
        lines.append(
            f"│  ├─ Landlord notified: {self.current_issues.landlord_notified} "
            f"({self.current_issues.landlord_notified_how or '?'}) "
            f"{self.current_issues.landlord_notified_when or ''}"
        )
        lines.append(
            f"│  └─ Evidence paths: {', '.join(self.current_issues.evidence_paths) or '(none)'}"
        )
        lines.append("└─ Personal circumstances")
        lines.append(
            f"   ├─ Disability: {self.personal.disability_status.value}"
        )
        lines.append(f"   ├─ Income source: {self.personal.income_source or '(not provided)'}")
        lines.append(f"   ├─ Dependents: {self.personal.dependents or '(not provided)'}")
        lines.append(
            f"   └─ Housing market: {self.personal.housing_market_notes or '(not provided)'}"
        )
        if self.incomplete_fields:
            lines.append("")
            lines.append("Incomplete / required next:")
            for f in self.incomplete_fields:
                lines.append(f"  • {f}")
        lines.append("")
        lines.append(f"> {self.disclaimer}")
        return "\n".join(lines)


# Dispute window calendar days from service (rule-of-thumb from workbench triage demo)
# Re-verify on RTB / RTA; mailing may add deemed-service days.
_DISPUTE_DAYS: dict[NoticeType, int] = {
    NoticeType.TEN_DAY: 5,
    NoticeType.ONE_MONTH: 10,
    NoticeType.TWO_MONTH: 15,
    NoticeType.FOUR_MONTH: 15,
}


def dispute_days_for_notice(notice_type: NoticeType) -> Optional[int]:
    return _DISPUTE_DAYS.get(notice_type)


def calculate_dispute_deadline(
    date_received: str,
    notice_type: NoticeType,
    *,
    method: ServiceMethod = ServiceMethod.UNKNOWN,
) -> tuple[Optional[str], str, Optional[int]]:
    """
    Returns (deadline_iso, note, days).

    Does NOT fully implement deemed-service / holiday rules — flags assumptions.
    """
    days = dispute_days_for_notice(notice_type)
    if days is None:
        return (
            None,
            "Unknown notice type — cannot calculate dispute window. Identify notice form.",
            None,
        )
    try:
        start = date.fromisoformat(date_received[:10])
    except ValueError:
        return None, "Invalid date_received — use YYYY-MM-DD.", None

    # Placeholder: no automatic mail add-days without confirmed RTB deemed-service rule
    deadline = start + timedelta(days=days)
    notes = [
        f"Rule-of-thumb: {days} calendar days from date received for {notice_type.value} notice.",
        "Re-verify dispute period on RTB materials / RTA before relying.",
    ]
    if method == ServiceMethod.MAILED:
        notes.append(
            "MAILED service: deemed-receipt rules may add days — do not treat this date as final."
        )
    if method == ServiceMethod.UNKNOWN:
        notes.append("Service method unknown — deadline may shift under deemed-service rules.")
    return deadline.isoformat(), " ".join(notes), days


def completeness_check(intake: TenancyIntake) -> list[str]:
    """Fields still needed before a solid matter open."""
    missing: list[str] = []
    if not intake.property_address.strip():
        missing.append("property_address")
    if not intake.unit_designation.strip():
        missing.append("unit_designation")
    if not intake.tenancy_start_date:
        missing.append("tenancy_start_date")
    if not intake.current_rent:
        missing.append("current_rent")
    if not intake.lease_names:
        missing.append("lease_names")
    if intake.notice.received:
        if not intake.notice.date_received:
            missing.append("notice.date_received")
        if intake.notice.notice_type == NoticeType.UNKNOWN:
            missing.append("notice.notice_type")
        if intake.notice.dispute_filed is None:
            missing.append("notice.dispute_filed")
        if intake.notice.dispute_filed is False and not intake.notice.dispute_deadline:
            missing.append("notice.dispute_deadline (set notice type + date)")
    if not intake.current_issues.categories and not intake.current_issues.narrative:
        missing.append("current_issues")
    if (
        intake.personal.disability_status == DisabilityStatus.YES
        and not intake.personal.consent_to_store_sensitive
    ):
        missing.append("personal.consent_to_store_sensitive (required if disability notes stored)")
    return missing
