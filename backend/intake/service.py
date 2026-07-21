"""Persist tenancy intake and refresh dispute deadlines."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from architecture.intake import (
    NoticeType,
    ServiceMethod,
    TenancyIntake,
    calculate_dispute_deadline,
    completeness_check,
)


def _path(root: Path, matter_id: str) -> Path:
    return root / matter_id / "intake.json"


def refresh_deadlines(intake: TenancyIntake) -> TenancyIntake:
    """Recalculate dispute deadline when notice received and not yet filed."""
    n = intake.notice
    if n.received and n.date_received and n.dispute_filed is not True:
        deadline, note, days = calculate_dispute_deadline(
            n.date_received,
            n.notice_type,
            method=n.method,
        )
        n.dispute_deadline = deadline
        n.dispute_deadline_note = note
        n.days_to_dispute = days
    intake.incomplete_fields = completeness_check(intake)
    intake.updated_at = datetime.now().isoformat(timespec="seconds")
    return intake


def save_intake(
    intake: TenancyIntake,
    *,
    root: Optional[Path] = None,
) -> Path:
    if not intake.matter_id:
        raise ValueError("intake.matter_id required")
    base = (root or Path("matters")).resolve()
    intake = refresh_deadlines(intake)
    d = base / intake.matter_id
    d.mkdir(parents=True, exist_ok=True)
    path = _path(base, intake.matter_id)
    path.write_text(
        json.dumps(intake.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tree = d / "intake_tree.md"
    tree.write_text(intake.format_tree(), encoding="utf-8")
    return path


def load_intake(
    matter_id: str,
    *,
    root: Optional[Path] = None,
) -> TenancyIntake:
    base = (root or Path("matters")).resolve()
    path = _path(base, matter_id)
    data = json.loads(path.read_text(encoding="utf-8"))
    intake = TenancyIntake.from_dict(data)
    return refresh_deadlines(intake)


def apply_intake_to_matter_meta(session: Any, intake: TenancyIntake) -> None:
    """Push core fields into MatterSession meta + claimed tags."""
    parties = list(intake.lease_names)
    title = (
        f"Tenancy — {intake.property_address} unit {intake.unit_designation}".strip()
    )
    tags: list[str] = []
    for c in intake.current_issues.categories:
        tags.append(c.value)
    if intake.notice.received:
        tags.append("retaliatory_eviction")  # soft; may refine
    session.update(
        title=title if intake.property_address else session.meta.title,
        parties=parties or session.meta.parties,
        tribunal_or_court="RTB",
        claimed_tags=list(dict.fromkeys(tags + list(session.meta.claimed_tags))),
    )


def intake_from_flat_answers(answers: dict[str, Any], *, matter_id: str) -> TenancyIntake:
    """
    Build TenancyIntake from a flat dict (form / chat answers).

    Keys mirror the tree (property_address, unit_designation, notice_received, …).
    """
    from architecture.intake import (
        CurrentIssue,
        IssueCategory,
        NoticeIntake,
        PersonalCircumstances,
        DisabilityStatus,
        PriorProceeding,
    )

    notice = NoticeIntake(
        received=bool(answers.get("notice_received", False)),
        date_received=answers.get("notice_date_received"),
        method=ServiceMethod(answers.get("notice_method", "unknown")),
        notice_type=NoticeType(answers.get("notice_type", "unknown")),
        notice_type_label=str(answers.get("notice_type_label") or ""),
        upload_paths=list(answers.get("notice_uploads") or []),
        dispute_filed=answers.get("dispute_filed"),
        dispute_filed_date=answers.get("dispute_filed_date"),
        dispute_file_number=answers.get("dispute_file_number"),
    )
    cats = []
    for c in answers.get("issue_categories") or []:
        try:
            cats.append(IssueCategory(c))
        except ValueError:
            cats.append(IssueCategory.OTHER)
    issues = CurrentIssue(
        categories=cats,
        category_other=str(answers.get("issue_other") or ""),
        timeline_start=answers.get("issue_start"),
        ongoing=bool(answers.get("issue_ongoing", True)),
        narrative=str(answers.get("issue_narrative") or ""),
        evidence_paths=list(answers.get("issue_evidence") or []),
        landlord_notified=answers.get("landlord_notified"),
        landlord_notified_how=str(answers.get("landlord_notified_how") or ""),
        landlord_notified_when=answers.get("landlord_notified_when"),
    )
    personal = PersonalCircumstances(
        disability_status=DisabilityStatus(
            answers.get("disability_status", "unknown")
        ),
        disability_notes=str(answers.get("disability_notes") or ""),
        income_source=str(answers.get("income_source") or ""),
        dependents=str(answers.get("dependents") or ""),
        housing_market_notes=str(answers.get("housing_market") or ""),
        consent_to_store_sensitive=bool(answers.get("consent_sensitive", False)),
    )
    priors = [
        PriorProceeding.from_dict(p) for p in (answers.get("prior_proceedings") or [])
    ]
    names = answers.get("lease_names") or []
    if isinstance(names, str):
        names = [n.strip() for n in names.split(",") if n.strip()]

    intake = TenancyIntake(
        matter_id=matter_id,
        property_address=str(answers.get("property_address") or ""),
        unit_designation=str(answers.get("unit_designation") or ""),
        tenancy_start_date=answers.get("tenancy_start_date"),
        current_rent=answers.get("current_rent"),
        lease_names=list(names),
        notice=notice,
        prior_proceedings=priors,
        current_issues=issues,
        personal=personal,
    )
    return refresh_deadlines(intake)
