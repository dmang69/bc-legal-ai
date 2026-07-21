"""
Case dashboard snapshot — Judicial Review of RTB Decision
File: KAM-S-S-65285

Planning status only. Confirm deadlines and assessments with counsel.
as_of=2026-01-20 yields ~60 days to 2026-03-21 (matches principal snapshot).
"""

from __future__ import annotations

from architecture.case_status import (
    CaseDashboard,
    CaseType,
    DeadlineItem,
    DeadlinePriority,
    GroundStatus,
    GroundStrength,
    MissingItem,
    NextAction,
    NextActionState,
    WorkflowStatus,
)


def kam_s_s_65285_dashboard(*, matter_id: str | None = None) -> CaseDashboard:
    return CaseDashboard(
        dashboard_id="DASH-KAM-S-S-65285",
        case_title="Judicial Review of RTB Decision",
        file_number="KAM-S-S-65285",
        case_type=CaseType.JUDICIAL_REVIEW,
        matter_id=matter_id or "KAM-S-S-65285",
        workflow_status=WorkflowStatus.DRAFTING,
        status_label="Petition drafting in progress",
        deadline="2026-03-21",
        deadline_label="Petition / JR filing window (confirm JRPA / applicable limitation)",
        as_of="2026-01-20",  # snapshot for "60 days remaining" display
        next_action=NextAction(
            description="Review draft petition",
            state=NextActionState.PENDING,
        ),
        evidence_complete_pct=85,
        missing_items=[
            MissingItem(
                label="Audio recording of RTB hearing",
                status_note="requested",
                blocking=False,
            ),
            MissingItem(
                label="Written RTB decision",
                status_note="awaiting from RTB",
                blocking=True,
            ),
        ],
        legal_grounds=[
            GroundStatus(
                label="Patent unreasonableness",
                strength=GroundStrength.STRONG,
                related_ground_ids=["1", "1a", "1b", "1c"],
            ),
            GroundStatus(
                label="Procedural fairness violation",
                strength=GroundStrength.MODERATE,
                related_ground_ids=["2", "2a", "2b"],
            ),
            GroundStatus(
                label="Error of law (s. 47 analysis)",
                strength=GroundStrength.STRONG,
                notes="Confirm s. 47 pin and analysis on BC Laws before filing",
            ),
            GroundStatus(
                label="Bias",
                strength=GroundStrength.INSUFFICIENT_EVIDENCE,
            ),
        ],
        strength_assessment_note="[Full assessment requires lawyer review]",
        upcoming_deadlines=[
            DeadlineItem(
                title="File judicial review petition",
                priority=DeadlinePriority.CRITICAL,
                due="2026-03-21",
                due_note="Confirm limitation under JRPA / applicable rules",
            ),
            DeadlineItem(
                title="Request RTB hearing audio recording",
                priority=DeadlinePriority.IMPORTANT,
                due="ASAP",
                due_note="processing takes 2-4 weeks",
            ),
            DeadlineItem(
                title="Organize evidence binder (drafts 1-3)",
                priority=DeadlinePriority.ROUTINE,
                due="2026-02-15",
            ),
        ],
        notes=(
            "Links to petition outline PET-JR-RTB-001 and examination EXAM-CROSS-SANGHERA-001. "
            "Deadline date and days remaining are planning figures — verify limitation "
            "period and any extensions under JRPA / applicable rules."
        ),
    )
