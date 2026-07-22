"""
Phase 3 contract validators — consent, exception, approval, knowledge_source.

Enforces design locks at serialization time.
Not legal advice.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


FORBIDDEN_CONSENT_KEYS = frozenset(
    {
        "privilege_class",
        "privilege_status",
        "waiver",
        "waived",
        "litigation_privilege",
        "solicitor_client",
    }
)


@dataclass
class ConsentContract:
    consent_id: str
    matter_id: str
    subject_id: str
    category: str
    purpose: str
    processing_scope: list[str]
    model_scope: str
    status: str
    notice_version: str
    granted_at: Optional[str] = None
    expires_at: Optional[str] = None
    withdrawn_at: Optional[str] = None
    captured_by: str = "system"
    authentication_event: Optional[str] = None
    signature_hash: Optional[str] = None
    plain_language: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for k in FORBIDDEN_CONSENT_KEYS:
            if k in d:
                raise ValueError(f"Consent contract forbids field {k} (consent ≠ privilege)")
        return d

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ConsentContract":
        for k in FORBIDDEN_CONSENT_KEYS:
            if k in data:
                raise ValueError(f"Consent payload forbids field {k} (consent ≠ privilege)")
        return ConsentContract(
            consent_id=str(data["consent_id"]),
            matter_id=str(data["matter_id"]),
            subject_id=str(data["subject_id"]),
            category=str(data["category"]),
            purpose=str(data["purpose"]),
            processing_scope=list(data.get("processing_scope") or []),
            model_scope=str(data.get("model_scope") or "PRIVATE_INFERENCE_ONLY"),
            status=str(data["status"]),
            notice_version=str(data["notice_version"]),
            granted_at=data.get("granted_at"),
            expires_at=data.get("expires_at"),
            withdrawn_at=data.get("withdrawn_at"),
            captured_by=str(data.get("captured_by") or "system"),
            authentication_event=data.get("authentication_event"),
            signature_hash=data.get("signature_hash"),
            plain_language=str(data.get("plain_language") or ""),
        )


@dataclass
class ExceptionContract:
    exception_id: str
    matter_id: str
    category: str
    severity: str
    summary: str
    status: str
    raw_client_content_logged: bool = False
    affected_artifacts: list[str] = field(default_factory=list)
    task_id: Optional[str] = None
    detected_by: str = "system"
    model_id: Optional[str] = None
    prompt_template_version: Optional[str] = None
    assigned_reviewer: Optional[str] = None
    resolution: Optional[str] = None
    resolution_by: Optional[str] = None
    freeze_export: bool = False
    block_workflow: bool = False
    proposed_content_quarantined: bool = False
    created_at: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        if self.raw_client_content_logged:
            raise ValueError("raw_client_content_logged must be false")
        return asdict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ExceptionContract":
        if data.get("raw_client_content_logged"):
            raise ValueError("Exceptions must not log raw client content")
        return ExceptionContract(
            exception_id=str(data.get("exception_id") or data.get("event_id")),
            matter_id=str(data["matter_id"]),
            category=str(data.get("category") or data.get("kind")),
            severity=str(data["severity"]),
            summary=str(data.get("summary") or data.get("message") or ""),
            status=str(data.get("status") or "OPEN"),
            raw_client_content_logged=False,
            affected_artifacts=list(data.get("affected_artifacts") or []),
            task_id=data.get("task_id"),
            detected_by=str(data.get("detected_by") or "system"),
            model_id=data.get("model_id"),
            prompt_template_version=data.get("prompt_template_version"),
            assigned_reviewer=data.get("assigned_reviewer"),
            resolution=data.get("resolution"),
            resolution_by=data.get("resolution_by"),
            freeze_export=bool(data.get("freeze_export", False)),
            block_workflow=bool(data.get("block_workflow", False)),
            proposed_content_quarantined=bool(
                data.get("proposed_content_quarantined", False)
            ),
            created_at=data.get("created_at") or data.get("ts"),
        )


@dataclass
class ApprovalContract:
    approval_id: str
    production_id: str
    matter_id: str
    stage: str
    actor_id: str
    decision: str
    snapshot_hash: str
    notes: str = ""
    ts: str = ""

    def to_dict(self) -> dict[str, Any]:
        if self.stage not in ("REVIEW", "APPROVE"):
            raise ValueError("stage must be REVIEW or APPROVE")
        if len(self.snapshot_hash) < 16:
            raise ValueError("snapshot_hash required")
        return asdict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ApprovalContract":
        return ApprovalContract(
            approval_id=str(data["approval_id"]),
            production_id=str(data["production_id"]),
            matter_id=str(data["matter_id"]),
            stage=str(data["stage"]),
            actor_id=str(data["actor_id"]),
            decision=str(data["decision"]),
            snapshot_hash=str(data["snapshot_hash"]),
            notes=str(data.get("notes") or ""),
            ts=str(data.get("ts") or ""),
        )


@dataclass
class KnowledgeSourceContract:
    source_id: str
    name: str
    authority_type: str
    jurisdiction: str
    permitted_content: list[str]
    retrieval_method: str = "approved_connector"
    health_status: str = "UNKNOWN"
    terms_reviewed_at: Optional[str] = None
    last_successful_update: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        if self.authority_type not in ("OFFICIAL_PRIMARY", "SECONDARY"):
            raise ValueError("authority_type invalid")
        return asdict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "KnowledgeSourceContract":
        return KnowledgeSourceContract(
            source_id=str(data["source_id"]),
            name=str(data["name"]),
            authority_type=str(data["authority_type"]),
            jurisdiction=str(data["jurisdiction"]),
            permitted_content=list(data.get("permitted_content") or []),
            retrieval_method=str(data.get("retrieval_method") or "approved_connector"),
            health_status=str(data.get("health_status") or "UNKNOWN"),
            terms_reviewed_at=data.get("terms_reviewed_at"),
            last_successful_update=data.get("last_successful_update"),
        )


RTB_ARCHIVE_WARNING = (
    "RTB decision archive coverage is partial by historical publication ranges and "
    "categories. Absence from the archive is not proof that no decision exists. "
    "See official BC government decision-search guidance."
)


@dataclass
class RtbDecisionContract:
    decision_id: str
    citation_or_file: str = ""
    publication_source: str = "BC_RTB_ARCHIVE"
    archive_coverage: str = "PARTIAL"
    precedential_weight: str = "NON_BINDING_TRIBUNAL"
    completeness_warning: str = RTB_ARCHIVE_WARNING
    official_url: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        if self.archive_coverage != "PARTIAL":
            raise ValueError("archive_coverage must remain PARTIAL (incomplete corpus)")
        d = asdict(self)
        d["completeness_warning"] = RTB_ARCHIVE_WARNING
        return d
