"""Backward-compatible facade + lifecycle orchestrator for Layer 6. """

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from services.post_resolution.compliance_monitor.monitor import ComplianceMonitor
from services.post_resolution.destruction.workflow import DestructionService
from services.post_resolution.enforcement.packages import EnforcementPackager
from services.post_resolution.escalation_router.router import EscalationRouter
from services.post_resolution.jr_pipeline.pipeline import JrPipeline
from services.post_resolution.outcome_tracker.engine import OutcomeTracker
from services.post_resolution.retention.schedule import RetentionScheduleEngine
from services.post_resolution.stay_generator.stay import StayGenerator


@dataclass
class OutcomeRecord:
    """Legacy simple outcome row — prefer OutcomeTracker."""

    matter_id: str
    decision_date: Optional[str] = None
    outcome_summary: str = ""
    predicted_summary: str = ""
    compliance_notes: str = ""
    retention_class: str = "litigation_hold"

    def to_dict(self) -> dict[str, Any]:
        return {
            "matter_id": self.matter_id,
            "decision_date": self.decision_date,
            "outcome_summary": self.outcome_summary,
            "predicted_summary": self.predicted_summary,
            "compliance_notes": self.compliance_notes,
            "retention_class": self.retention_class,
        }


@dataclass
class PostResolutionEngine:
    """Wires all 4-4 subsystems for a matter lifecycle."""

    outcomes: OutcomeTracker = field(default_factory=OutcomeTracker)
    compliance: ComplianceMonitor = field(default_factory=ComplianceMonitor)
    escalations: EscalationRouter = field(default_factory=EscalationRouter)
    enforcement: EnforcementPackager = field(default_factory=EnforcementPackager)
    jr: JrPipeline = field(default_factory=JrPipeline)
    stays: StayGenerator = field(default_factory=StayGenerator)
    retention: RetentionScheduleEngine = field(default_factory=RetentionScheduleEngine)
    destruction: DestructionService = field(default_factory=DestructionService)

    def __post_init__(self) -> None:
        self.destruction.schedule = self.retention

    def ingest_decision(
        self,
        *,
        matter_id: str,
        text: str,
        decision_date: Optional[str] = None,
        predicted_summary: str = "",
        predicted_classes: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        if predicted_summary or predicted_classes:
            self.outcomes.set_prediction(
                matter_id,
                summary=predicted_summary,
                classes=predicted_classes or [],
            )
        rec = self.outcomes.ingest_decision_text(
            matter_id=matter_id, text=text, decision_date=decision_date
        )
        self.compliance.seed_from_tracker(self.outcomes, matter_id)
        return rec.to_dict()


# Alias used by older imports
PostResolutionStub = PostResolutionEngine
