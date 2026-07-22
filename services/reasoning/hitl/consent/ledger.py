"""
Consent ledger — purpose-specific grants, state machine, withdrawal without destroying holds.

Not legal advice. Consent ≠ privilege waiver.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from services.reasoning.hitl.consent.audit import ConsentAuditLog
from services.reasoning.hitl.consent.scopes import (
    ConsentScope,
    ConsentStatus,
    plain_language_for,
)
from services.reasoning.hitl.schemas.common import (
    ModelDestination,
    OperationDecision,
    ProcessingBasis,
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_scope(scope: ConsentScope | str) -> ConsentScope:
    if isinstance(scope, ConsentScope):
        # Resolve aliases to primary member with same value
        return ConsentScope(scope.value)
    s = str(scope).upper().replace("TENANCY_FACTS", "TENANCY_RECORDS")
    # map legacy strings
    legacy = {
        "TENANCY": "TENANCY_RECORDS",
        "MEDICAL": "MEDICAL_INFORMATION",
        "FINANCIAL": "FINANCIAL_INFORMATION",
        "PHOTOS": "PHOTOGRAPHS",
        "AUDIO": "AUDIO_RECORDINGS",
        "VIDEO": "VIDEO_RECORDINGS",
        "AI_PROCESSING": "AI_ANALYSIS",
        "CLOUD_PROCESSING": "CLOUD_STORAGE_IMPORT",
        "THIRD_PARTY_COMMS": "CLIENT_COMMUNICATION_ANALYSIS",
    }
    s = legacy.get(s, s)
    return ConsentScope(s)


@dataclass
class ConsentRecord:
    consent_id: str
    matter_id: str
    subject_id: str  # client
    category: ConsentScope
    purpose: str
    processing_scope: list[str]
    model_scope: str
    status: ConsentStatus
    granted_at: Optional[str] = None
    expires_at: Optional[str] = None
    notice_version: str = "privacy-notice-3.1"
    captured_by: str = "system"
    authentication_event: Optional[str] = None
    signature_hash: Optional[str] = None
    withdrawn_at: Optional[str] = None
    plain_language: str = ""
    version: str = "1"
    # legacy field names for tests
    client_id: str = ""
    scope: Optional[ConsentScope] = None
    granted: bool = False

    def __post_init__(self) -> None:
        if not self.client_id:
            self.client_id = self.subject_id
        if self.scope is None:
            self.scope = self.category
        self.granted = self.status in (
            ConsentStatus.GRANTED,
            ConsentStatus.ACTIVE,
            ConsentStatus.MODIFIED,
        )

    def active(self) -> bool:
        return self.status in (
            ConsentStatus.ACTIVE,
            ConsentStatus.GRANTED,
            ConsentStatus.MODIFIED,
            ConsentStatus.PROCESSING_PERMITTED_WITHOUT_CONSENT,
        ) and self.withdrawn_at is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "consent_id": self.consent_id,
            "matter_id": self.matter_id,
            "subject_id": self.subject_id,
            "client_id": self.client_id,
            "category": self.category.value,
            "scope": self.category.value,
            "purpose": self.purpose,
            "processing_scope": list(self.processing_scope),
            "model_scope": self.model_scope,
            "granted_at": self.granted_at,
            "expires_at": self.expires_at,
            "status": self.status.value,
            "notice_version": self.notice_version,
            "captured_by": self.captured_by,
            "authentication_event": self.authentication_event,
            "signature_hash": self.signature_hash,
            "withdrawn_at": self.withdrawn_at,
            "plain_language": self.plain_language,
            "version": self.version,
            "granted": self.granted,
            "active": self.active(),
        }


@dataclass
class WithdrawalPlan:
    """
    Withdrawal blocks optional AI immediately; does not unconditional-delete.

    BC PIPA: withdrawal generally operates on reasonable notice; processing may
    continue where authorized without consent or required by legal obligations.
    Confirm current PIPA text on BC Laws. Not legal advice.
    """

    consent_id: str
    matter_id: str
    block_new_ai_retrieval: bool = True
    cancel_queued_jobs: bool = True
    invalidate_capability_tokens: bool = True
    remove_from_ai_search: bool = True
    identify_derived_artifacts: list[str] = field(default_factory=list)
    legal_hold_blocks_destruction: bool = False
    privacy_review_required: bool = False
    schedule_deletion: bool = False
    unconditional_delete: bool = False  # always False under this design
    pipa_reasonable_notice: bool = True
    other_processing_basis_review: bool = True
    privilege_status_unchanged: bool = True
    client_consequences: str = ""
    steps_completed: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "consent_id": self.consent_id,
            "matter_id": self.matter_id,
            "block_new_ai_retrieval": self.block_new_ai_retrieval,
            "cancel_queued_jobs": self.cancel_queued_jobs,
            "invalidate_capability_tokens": self.invalidate_capability_tokens,
            "remove_from_ai_search": self.remove_from_ai_search,
            "identify_derived_artifacts": list(self.identify_derived_artifacts),
            "legal_hold_blocks_destruction": self.legal_hold_blocks_destruction,
            "privacy_review_required": self.privacy_review_required,
            "schedule_deletion": self.schedule_deletion,
            "unconditional_delete": False,
            "pipa_reasonable_notice": self.pipa_reasonable_notice,
            "other_processing_basis_review": self.other_processing_basis_review,
            "privilege_status_unchanged": True,
            "client_consequences": self.client_consequences,
            "steps_completed": list(self.steps_completed),
        }


@dataclass
class ConsentLedger:
    records: list[ConsentRecord] = field(default_factory=list)
    audit: ConsentAuditLog = field(default_factory=ConsentAuditLog)
    derived_index: dict[str, list[str]] = field(default_factory=dict)  # consent_id -> artifact ids
    legal_holds: set[str] = field(default_factory=set)  # matter_ids
    blocked_ai_matters: set[str] = field(default_factory=set)

    def grant(
        self,
        *,
        matter_id: str,
        client_id: str,
        scope: ConsentScope | str,
        purpose: str = "",
        processing_scope: Optional[list[str]] = None,
        model_scope: str = ModelDestination.PRIVATE_INFERENCE_ONLY.value,
        notice_version: str = "privacy-notice-3.1",
        captured_by: str = "client_portal",
        authentication_event: Optional[str] = None,
        signature_hash: Optional[str] = None,
        plain_language: str = "",
        subject_id: Optional[str] = None,
    ) -> ConsentRecord:
        sc = _normalize_scope(scope)
        subject = subject_id or client_id
        # supersede active same category
        for r in list(self.records):
            if r.matter_id == matter_id and r.category.value == sc.value and r.active():
                self.withdraw(r.consent_id, reason="superseded_by_new_grant", execute_plan=False)

        rec = ConsentRecord(
            consent_id=f"consent_{uuid4().hex[:12]}",
            matter_id=matter_id,
            subject_id=subject,
            category=sc,
            purpose=purpose or f"Process {sc.value} for matter {matter_id}",
            processing_scope=processing_scope or ["process", "link_to_evidence_matrix"],
            model_scope=model_scope,
            status=ConsentStatus.ACTIVE,
            granted_at=_utcnow(),
            notice_version=notice_version,
            captured_by=captured_by,
            authentication_event=authentication_event,
            signature_hash=signature_hash,
            plain_language=plain_language or plain_language_for(sc),
            client_id=client_id,
            scope=sc,
            granted=True,
        )
        self.records.append(rec)
        self.audit.append(
            matter_id=matter_id,
            client_id=client_id,
            action="GRANT",
            scope=sc.value,
            consent_id=rec.consent_id,
            detail=f"notice={notice_version}",
        )
        self.blocked_ai_matters.discard(matter_id)
        return rec

    def withdraw(
        self,
        consent_id: str,
        *,
        reason: str = "client_withdrawal",
        execute_plan: bool = True,
        derived_artifacts: Optional[list[str]] = None,
    ) -> Optional[ConsentRecord]:
        for r in self.records:
            if r.consent_id == consent_id and r.withdrawn_at is None:
                r.status = ConsentStatus.WITHDRAWAL_REQUESTED
                plan = self._build_withdrawal_plan(r, derived_artifacts or [])
                if execute_plan:
                    self._execute_withdrawal_plan(plan, r)
                r.status = ConsentStatus.WITHDRAWN
                r.withdrawn_at = _utcnow()
                r.granted = False
                self.audit.append(
                    matter_id=r.matter_id,
                    client_id=r.client_id,
                    action="WITHDRAW",
                    scope=r.category.value,
                    consent_id=r.consent_id,
                    detail=reason,
                )
                # Privilege status is NOT changed by withdrawal
                self.audit.append(
                    matter_id=r.matter_id,
                    client_id=r.client_id,
                    action="PRIVILEGE_UNCHANGED",
                    scope=r.category.value,
                    consent_id=r.consent_id,
                    detail="Withdrawal of processing consent does not change privilege status",
                )
                return r
        return None

    def _build_withdrawal_plan(
        self, rec: ConsentRecord, derived: list[str]
    ) -> WithdrawalPlan:
        hold = rec.matter_id in self.legal_holds
        return WithdrawalPlan(
            consent_id=rec.consent_id,
            matter_id=rec.matter_id,
            identify_derived_artifacts=derived or self.derived_index.get(rec.consent_id, []),
            legal_hold_blocks_destruction=hold,
            privacy_review_required=rec.category
            in (
                ConsentScope.MEDICAL_INFORMATION,
                ConsentScope.DISABILITY_INFORMATION,
                ConsentScope.EXTERNAL_MODEL_PROCESSING,
            ),
            # Deletion only scheduled after PIPA notice + basis review; never if hold
            schedule_deletion=False if hold else True,
            unconditional_delete=False,
            pipa_reasonable_notice=True,
            other_processing_basis_review=True,
            privilege_status_unchanged=True,
            client_consequences=(
                "Optional AI analysis for this category will stop immediately. "
                "Under BC privacy law, remaining disposition of personal information "
                "generally proceeds on reasonable notice and may continue where another "
                "lawful basis or legal obligation applies. Documents under legal hold "
                "or required for litigation are retained. Privilege is unchanged. "
                "Confirm current PIPA text on BC Laws."
            ),
        )

    def _execute_withdrawal_plan(self, plan: WithdrawalPlan, rec: ConsentRecord) -> None:
        steps = [
            "block_new_optional_ai_retrieval_immediate",
            "cancel_queued_optional_jobs_where_safe",
            "invalidate_unstarted_capability_tokens",
            "remove_from_ordinary_ai_search",
            "identify_derived_embeddings_summaries_nodes",
            "assess_legal_hold_and_retention",
            "assess_other_processing_basis_pipa",
            "inform_client_consequences_reasonable_notice",
            "immutable_withdrawal_record",
            "privilege_status_unchanged",
        ]
        if plan.privacy_review_required:
            steps.append("privacy_or_legal_review_flagged")
        if plan.legal_hold_blocks_destruction:
            steps.append("destruction_blocked_by_legal_hold")
        elif plan.schedule_deletion:
            steps.append("schedule_disposition_after_reasonable_notice_not_immediate_wipe")
        else:
            steps.append("no_auto_delete")
        assert plan.unconditional_delete is False
        plan.steps_completed = steps
        self.blocked_ai_matters.add(rec.matter_id)
        rec.status = ConsentStatus.RESTRICTED

    def withdraw_scope(
        self,
        *,
        matter_id: str,
        scope: ConsentScope | str,
        reason: str = "client_withdrawal",
    ) -> list[ConsentRecord]:
        sc = _normalize_scope(scope)
        out: list[ConsentRecord] = []
        for r in list(self.records):
            if r.matter_id == matter_id and r.category.value == sc.value and r.active():
                w = self.withdraw(r.consent_id, reason=reason)
                if w:
                    out.append(w)
        return out

    def active_scopes(self, matter_id: str) -> set[ConsentScope]:
        return {
            ConsentScope(r.category.value)
            for r in self.records
            if r.matter_id == matter_id and r.active()
        }

    def requires_scope(self, matter_id: str, scope: ConsentScope | str) -> bool:
        sc = _normalize_scope(scope)
        return not any(
            r.active() and r.category.value == sc.value
            for r in self.records
            if r.matter_id == matter_id
        )

    def has_scope(self, matter_id: str, scope: ConsentScope | str) -> bool:
        return not self.requires_scope(matter_id, scope)

    def history(self, matter_id: str) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self.records if r.matter_id == matter_id]

    def current_state(self, matter_id: str) -> dict[str, Any]:
        active = sorted({r.category.value for r in self.records if r.matter_id == matter_id and r.active()})
        # unique enum values only (no aliases)
        all_vals = sorted({s.value for s in ConsentScope})
        missing = sorted(set(all_vals) - set(active))
        return {
            "matter_id": matter_id,
            "active": active,
            "missing": missing,
            "ai_retrieval_blocked": matter_id in self.blocked_ai_matters,
            "audit_count": len(self.audit.for_matter(matter_id)),
            "consent_vs_privilege": {
                "consent_is_not_waiver": True,
                "withdrawal_does_not_change_privilege": True,
                "external_model_requires_separate_consent": True,
                "disclose_to_opposing_requires_privilege_review": True,
            },
        }

    def evaluate(
        self,
        *,
        matter_id: str,
        subject_id: str,
        data_categories: list[ConsentScope | str],
        purpose: str,
        model_destination: ModelDestination | str = ModelDestination.PRIVATE_INFERENCE_ONLY,
    ) -> OperationDecision:
        """POST /consents/evaluate-operation equivalent."""
        dest = (
            model_destination
            if isinstance(model_destination, ModelDestination)
            else ModelDestination(str(model_destination))
        )
        if dest == ModelDestination.PUBLIC_DEMO_FORBIDDEN:
            return OperationDecision(
                permitted=False,
                basis=ProcessingBasis.NONE,
                reasons=["Public demo destination forbidden for client matter data."],
            )
        if matter_id in self.blocked_ai_matters and dest != ModelDestination.NONE:
            return OperationDecision(
                permitted=False,
                basis=ProcessingBasis.NONE,
                reasons=["Optional AI retrieval blocked after consent withdrawal."],
            )

        cats = [_normalize_scope(c) for c in data_categories]
        missing = [c.value for c in cats if self.requires_scope(matter_id, c)]

        if dest == ModelDestination.EXTERNAL_MODEL:
            if self.requires_scope(matter_id, ConsentScope.EXTERNAL_MODEL_PROCESSING):
                missing.append(ConsentScope.EXTERNAL_MODEL_PROCESSING.value)

        privilege_review = ConsentScope.DISCLOSE_TO_OPPOSING.value in [
            c.value for c in cats
        ] or any("opposing" in purpose.lower() for _ in [0])

        if "opposing" in purpose.lower() or "disclose" in purpose.lower():
            privilege_review = True

        if missing:
            return OperationDecision(
                permitted=False,
                basis=ProcessingBasis.NONE,
                reasons=[f"Missing consent categories: {', '.join(missing)}"],
                required_consents=missing,
                privilege_review_required=privilege_review,
            )

        # AI analysis base for model work
        if dest != ModelDestination.NONE and self.requires_scope(
            matter_id, ConsentScope.AI_ANALYSIS
        ):
            return OperationDecision(
                permitted=False,
                basis=ProcessingBasis.NONE,
                reasons=["AI_ANALYSIS consent required for model destination."],
                required_consents=[ConsentScope.AI_ANALYSIS.value],
            )

        return OperationDecision(
            permitted=True,
            basis=ProcessingBasis.CONSENT,
            reasons=[f"Processing basis: consent for {purpose}"],
            privilege_review_required=privilege_review,
            metadata={"subject_id": subject_id, "destination": dest.value},
        )

    def place_legal_hold(self, matter_id: str) -> None:
        self.legal_holds.add(matter_id)
