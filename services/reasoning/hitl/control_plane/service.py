"""
HITL control plane — every material reasoning/output operation queries this first.

Policy enforcement service, not UI checkboxes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from services.reasoning.hitl.approvals.records import ApprovalRegistry
from services.reasoning.hitl.competency_gate.gate import CompetencyGate
from services.reasoning.hitl.competency_gate.profile import LawyerProfile
from services.reasoning.hitl.consent.ledger import ConsentLedger
from services.reasoning.hitl.consent.scopes import ConsentScope
from services.reasoning.hitl.exceptions.bus import ExceptionBus
from services.reasoning.hitl.privilege_check.production import (
    OutputClass,
    ProductionGate,
    ProductionPackage,
)
from services.reasoning.hitl.schemas.common import (
    ConsentGateBlocked,
    ModelDestination,
    OperationDecision,
    ProcessingBasis,
)


@dataclass
class HitlControlPlane:
    consents: ConsentLedger = field(default_factory=ConsentLedger)
    exceptions: ExceptionBus = field(default_factory=ExceptionBus)
    productions: ProductionGate = field(default_factory=ProductionGate)
    competency: CompetencyGate = field(default_factory=CompetencyGate)
    approvals: ApprovalRegistry = field(default_factory=ApprovalRegistry)

    def __post_init__(self) -> None:
        self.productions.approvals = self.approvals

    def authorize_processing(
        self,
        *,
        matter_id: str,
        subject_id: str,
        categories: list[ConsentScope | str],
        purpose: str,
        model_destination: ModelDestination = ModelDestination.PRIVATE_INFERENCE_ONLY,
    ) -> OperationDecision:
        if self.exceptions.export_frozen(matter_id):
            return OperationDecision(
                permitted=False,
                basis=ProcessingBasis.NONE,
                reasons=["Matter frozen due to CRITICAL exception."],
                freeze_export=True,
            )
        return self.consents.evaluate(
            matter_id=matter_id,
            subject_id=subject_id,
            data_categories=categories,
            purpose=purpose,
            model_destination=model_destination,
        )

    def require_processing(self, **kwargs: Any) -> OperationDecision:
        d = self.authorize_processing(**kwargs)
        if not d.permitted:
            raise ConsentGateBlocked(d.reasons)
        return d

    def authorize_output(
        self,
        *,
        matter_id: str,
        output_class: OutputClass | str,
        body: str,
        document_ids: Optional[list[str]] = None,
        derivative_texts: Optional[list[str]] = None,
        recipient: str = "",
        reviewer: Optional[LawyerProfile] = None,
        task_type: Optional[str] = None,
    ) -> ProductionPackage:
        competency_ok = True
        if reviewer:
            dec = self.competency.evaluate(
                reviewer, matter_id=matter_id, task_type=task_type
            )
            competency_ok = dec.allowed
            if not dec.allowed:
                self.exceptions.emit(
                    matter_id=matter_id,
                    kind="COMPETENCY_GATE_FAILURE",
                    message="; ".join(dec.reasons),
                )
        return self.productions.freeze(
            matter_id=matter_id,
            output_class=output_class,
            body=body,
            document_ids=document_ids,
            derivative_texts=derivative_texts,
            recipient=recipient,
            critical_exception_open=self.exceptions.export_frozen(matter_id),
            competency_ok=competency_ok,
        )
