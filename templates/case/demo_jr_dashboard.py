"""
SYNTHETIC demonstration dashboard only.

No real court file numbers, parties, or live deadlines.
Label: DEMO-JR-0001 — fictional JR workbench snapshot for tests and docs.
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

# Fixed synthetic "as of" for stable demo math — not a live clock.
_DEMO_AS_OF = "2026-01-15"
_DEMO_DEADLINE = "2026-03-16"  # illustrative 60-day window from as_of (synthetic)


def demo_jr_dashboard(*, matter_id: str | None = None) -> CaseDashboard:
    return CaseDashboard(
        dashboard_id="DASH-DEMO-JR-0001",
        case_title="[SYNTHETIC] Judicial Review of Tribunal Decision — Demo Matter",
        file_number="DEMO-JR-0001",
        case_type=CaseType.JUDICIAL_REVIEW,
        matter_id=matter_id or "DEMO-JR-0001",
        workflow_status=WorkflowStatus.DRAFTING,
        status_label="[SYNTHETIC] Petition drafting in progress",
        deadline=_DEMO_DEADLINE,
        deadline_label=(
            "[SYNTHETIC] Illustrative JR filing window only — "
            "not a live matter; use deadline engine + counsel confirmation for real files"
        ),
        as_of=_DEMO_AS_OF,
        next_action=NextAction(
            description="[SYNTHETIC] Review draft petition outline",
            state=NextActionState.PENDING,
        ),
        evidence_complete_pct=40,
        missing_items=[
            MissingItem(
                label="[SYNTHETIC] Hearing audio (placeholder)",
                status_note="demo only",
                blocking=False,
            ),
            MissingItem(
                label="[SYNTHETIC] Written tribunal decision (placeholder)",
                status_note="demo only",
                blocking=True,
            ),
        ],
        legal_grounds=[
            GroundStatus(
                label="Reasonableness / patent unreasonableness framing (demo)",
                strength=GroundStrength.MODERATE,
                related_ground_ids=["1"],
            ),
            GroundStatus(
                label="Procedural fairness (demo)",
                strength=GroundStrength.MODERATE,
                related_ground_ids=["2"],
            ),
            GroundStatus(
                label="Error of law (demo pin — verify statute before any filing)",
                strength=GroundStrength.INSUFFICIENT_EVIDENCE,
            ),
        ],
        strength_assessment_note="[SYNTHETIC] Full assessment requires lawyer review on a real matter.",
        upcoming_deadlines=[
            DeadlineItem(
                title="[SYNTHETIC] Illustrative petition deadline",
                priority=DeadlinePriority.CRITICAL,
                due=_DEMO_DEADLINE,
                due_note="Synthetic date for UI demo only — not a live limitation clock",
            ),
            DeadlineItem(
                title="[SYNTHETIC] Request record materials",
                priority=DeadlinePriority.IMPORTANT,
                due="ASAP",
                due_note="demo workflow step",
            ),
        ],
        notes=(
            "SYNTHETIC DEMO ONLY. No real parties, file numbers, or live deadlines. "
            "For real JR limitation use services.deadlines.jr_clock (60 days from "
            "issuance of final decision; ATA s.57(2) extension is counsel-driven). "
            "Petition form is Form 66 (not Form 67)."
        ),
    )


# Back-compat name used by older call sites (now synthetic)
def kam_s_s_65285_dashboard(*, matter_id: str | None = None) -> CaseDashboard:
    return demo_jr_dashboard(matter_id=matter_id or "DEMO-JR-0001")
