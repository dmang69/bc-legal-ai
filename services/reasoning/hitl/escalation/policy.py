"""Escalation policy matrix per architecture severity model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.reasoning.hitl.exceptions.kinds import Severity


@dataclass
class EscalationPolicy:
    def response_for(self, severity: Severity) -> dict[str, Any]:
        if severity == Severity.CRITICAL:
            return {
                "notify_supervising_lawyer": True,
                "notify_security_privacy_when_applicable": True,
                "freeze_export": True,
                "preserve_evidence": True,
                "require_written_resolution": True,
                "ai_may_dismiss": False,
            }
        if severity == Severity.HIGH:
            return {
                "block_affected_workflow": True,
                "assign_qualified_reviewer": True,
                "ai_may_dismiss": False,
            }
        if severity == Severity.WARNING:
            return {
                "unresolved_marker_in_draft": True,
                "require_review_before_finalization": True,
            }
        if severity == Severity.NOTICE:
            return {"add_to_review_report": True}
        return {"record_only": True}
