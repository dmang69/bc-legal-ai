"""Compatibility re-export."""

from services.reasoning.hitl.privilege_check.scan import (
    PrivilegePreservationResult,
    scan_pre_output,
)

__all__ = ["PrivilegePreservationResult", "scan_pre_output"]
