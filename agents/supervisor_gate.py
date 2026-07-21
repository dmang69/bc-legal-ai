"""Supervising Counsel Gate — blocks high-risk actions without express approval."""

from __future__ import annotations

from architecture.schemas import ApprovalAction, ReviewReport


BLOCKED_WITHOUT_APPROVAL = set(ApprovalAction)


def require_approval(action: ApprovalAction, approved: bool, note: str = "") -> None:
    if action in BLOCKED_WITHOUT_APPROVAL and not approved:
        raise PermissionError(
            f"Human approval required for action: {action.value}"
            + (f" ({note})" if note else "")
        )


def finalize_package(
    report: ReviewReport,
    authorities_clean: bool,
    human_approved: bool,
) -> ReviewReport:
    if report.unverified_authorities > 0 or not authorities_clean:
        raise PermissionError("Cannot finalize: citation audit incomplete.")
    if not human_approved:
        raise PermissionError("Cannot finalize: human approval REQUIRED.")
    report.human_approval = "APPROVED"
    return report
