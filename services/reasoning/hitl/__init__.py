"""
HITL control plane packages:

  consent/ exceptions/ privilege_check/ competency_gate/
  approvals/ escalation/ schemas/ control_plane/
"""

from services.reasoning.hitl.competency_gate import CompetencyDecision, CompetencyGate, LawyerProfile
from services.reasoning.hitl.consent import ConsentLedger, ConsentScope
from services.reasoning.hitl.control_plane import HitlControlPlane
from services.reasoning.hitl.exceptions import ExceptionBus, ExceptionKind, Severity
from services.reasoning.hitl.privilege_check import (
    PrivilegePreservationResult,
    PrivilegeReviewWorkflow,
    ProductionGate,
    scan_pre_output,
)

__all__ = [
    "ConsentLedger",
    "ConsentScope",
    "ExceptionBus",
    "ExceptionKind",
    "Severity",
    "PrivilegePreservationResult",
    "PrivilegeReviewWorkflow",
    "ProductionGate",
    "scan_pre_output",
    "CompetencyGate",
    "CompetencyDecision",
    "LawyerProfile",
    "HitlControlPlane",
]
