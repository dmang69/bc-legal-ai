"""
Phase 4-4 — Full Post-Resolution Lifecycle Engine (Layer 6).

Subsystems:
  outcome_tracker, obligation_parser, compliance_monitor, escalation_router,
  enforcement, jr_pipeline, stay_generator, retention, destruction
"""

from services.post_resolution.outcome_tracker import OutcomeTracker, OutcomeTrackingRecord
from services.post_resolution.obligation_parser import parse_decision_text
from services.post_resolution.compliance_monitor import ComplianceMonitor
from services.post_resolution.escalation_router import EscalationRouter
from services.post_resolution.enforcement import EnforcementPackager
from services.post_resolution.jr_pipeline import JrPipeline
from services.post_resolution.stay_generator import StayGenerator
from services.post_resolution.retention import RetentionScheduleEngine
from services.post_resolution.destruction import DestructionService

# Backward-compatible thin types
from services.post_resolution.service import OutcomeRecord, PostResolutionStub

__all__ = [
    "OutcomeTracker",
    "OutcomeTrackingRecord",
    "parse_decision_text",
    "ComplianceMonitor",
    "EscalationRouter",
    "EnforcementPackager",
    "JrPipeline",
    "StayGenerator",
    "RetentionScheduleEngine",
    "DestructionService",
    "OutcomeRecord",
    "PostResolutionStub",
]
