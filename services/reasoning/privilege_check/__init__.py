"""Compatibility shim — prefer services.reasoning.hitl.privilege_check."""

from services.reasoning.hitl.privilege_check import (
    PrivilegePreservationResult,
    PrivilegeReviewWorkflow,
    scan_evidence_bundle,
    scan_pre_output,
)

__all__ = [
    "PrivilegePreservationResult",
    "PrivilegeReviewWorkflow",
    "scan_pre_output",
    "scan_evidence_bundle",
]
