"""
Production gate — blocks export / filing / opposing production of protected privilege.

Court destination does not bypass this gate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from architecture.privilege_schemas import (
    PROTECTED_FOR_EXPORT,
    PrincipalRole,
    PrivilegeMetadata,
    PrivilegeStatus,
    WaiverEvent,
)
from architecture.schemas import ApprovalAction
from agents.supervisor_gate import require_approval


@dataclass
class ExportItem:
    document_id: str
    privilege: PrivilegeMetadata


@dataclass
class ProductionDecision:
    allowed: bool
    blocked_document_ids: list[str] = field(default_factory=list)
    requires_lawyer_signoff: bool = False
    requires_client_waiver_signoff: bool = False
    review_queue: bool = False
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "blocked_document_ids": list(self.blocked_document_ids),
            "requires_lawyer_signoff": self.requires_lawyer_signoff,
            "requires_client_waiver_signoff": self.requires_client_waiver_signoff,
            "review_queue": self.review_queue,
            "reasons": list(self.reasons),
        }


def run_production_gate(
    items: Iterable[ExportItem],
    *,
    instructing_lawyer_signed: bool = False,
    client_waiver_signed: bool = False,
    intended_waiver: bool = False,
    destination: str = "export",  # export | opposing | tribunal
) -> ProductionDecision:
    """
    Mandatory before ANY document leaves the system.

    1. Scan privilege tags
    2. Block CLAIMED/ASSERTED/UPHELD without lawyer sign-off
    3. Intended waiver requires client_principal sign-off + WaiverEvent on records
    4. Same gate for tribunal filings
    """
    blocked: list[str] = []
    reasons: list[str] = []
    protected_found = False

    for item in items:
        st = item.privilege.privilege_status
        if st in PROTECTED_FOR_EXPORT:
            protected_found = True
            blocked.append(item.document_id)
            reasons.append(
                f"{item.document_id}: {st.value} "
                f"(basis={item.privilege.privilege_basis.value}) blocked for {destination}"
            )
        if not item.privilege.human_confirmed and item.privilege.privilege_basis.value != "none":
            # Unconfirmed tags: treat as high risk for production
            if item.document_id not in blocked:
                blocked.append(item.document_id)
            reasons.append(f"{item.document_id}: privilege tag not human-confirmed")
            protected_found = True

    if intended_waiver:
        if not client_waiver_signed:
            return ProductionDecision(
                allowed=False,
                blocked_document_ids=blocked,
                requires_client_waiver_signoff=True,
                review_queue=True,
                reasons=reasons
                + ["Intended waiver requires client_principal cryptographic sign-off"],
            )
        # Client signed: still require lawyer to run the release
        if not instructing_lawyer_signed:
            return ProductionDecision(
                allowed=False,
                blocked_document_ids=blocked,
                requires_lawyer_signoff=True,
                requires_client_waiver_signoff=False,
                review_queue=True,
                reasons=reasons + ["Waiver release still requires instructing_lawyer sign-off"],
            )
        return ProductionDecision(
            allowed=True,
            blocked_document_ids=[],
            reasons=["Client waiver + lawyer sign-off accepted; ensure WaiverEvent logged per doc"],
        )

    if protected_found and not instructing_lawyer_signed:
        return ProductionDecision(
            allowed=False,
            blocked_document_ids=blocked,
            requires_lawyer_signoff=True,
            review_queue=True,
            reasons=reasons
            + ["Instructing lawyer sign-off required before production of protected material"],
        )

    if protected_found and instructing_lawyer_signed:
        # Lawyer may produce non-privileged only if they reclassified — still block protected
        # unless intended_waiver path was used
        still = [
            i.document_id
            for i in items
            if i.privilege.privilege_status in PROTECTED_FOR_EXPORT
        ]
        if still:
            return ProductionDecision(
                allowed=False,
                blocked_document_ids=still,
                requires_client_waiver_signoff=True,
                review_queue=True,
                reasons=[
                    "Protected privilege present: set intended_waiver=True with client sign-off, "
                    "or reclassify after privilege review"
                ],
            )

    return ProductionDecision(allowed=True, reasons=["Production gate clear"])


def assert_waive_privilege_action(
    *,
    client_approved: bool,
    lawyer_approved: bool,
) -> None:
    """Supervisor gate for WAIVE_PRIVILEGE — both client and lawyer."""
    require_approval(ApprovalAction.WAIVE_PRIVILEGE, approved=client_approved, note="client")
    require_approval(
        ApprovalAction.WAIVE_PRIVILEGE,
        approved=lawyer_approved,
        note="instructing_lawyer",
    )


def clawback_letter_scaffold(
    *,
    produced_document_ids: list[str],
    produced_to: str,
    produced_when: str,
    authorized_by: str,
) -> str:
    """
    Template only — verify current BC Supreme Court Civil Rules / forms before filing.
    Do not treat rule numbers in this scaffold as authority without official check.
    """
    docs = ", ".join(produced_document_ids) or "(none listed)"
    return f"""\
PRIVILEGE CLAWBACK — DRAFT TEMPLATE (NOT A FILED DOCUMENT)

Produced materials: {docs}
Produced to: {produced_to}
Produced when: {produced_when}
Authorization recorded as: {authorized_by}

[Counsel to complete: basis of privilege, request for return/destruction,
non-use, and any applicable Civil Rules procedure — VERIFY current Rules.]

This template was auto-generated by ALA for lawyer review only.
"""
