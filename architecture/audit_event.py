"""
Immutable audit events for ALA workbench actions.

Example: EVIDENCE_NODE_CREATED with chain_of_custody and extraction details.
Not legal advice. Audit logs support accountability; retain per policy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class ActorType(str, Enum):
    AI_ENGINE = "AI_ENGINE"
    HUMAN_USER = "HUMAN_USER"
    SYSTEM = "SYSTEM"
    LAWYER = "LAWYER"
    CLIENT = "CLIENT"


class AuditAction(str, Enum):
    EVIDENCE_NODE_CREATED = "EVIDENCE_NODE_CREATED"
    EVIDENCE_NODE_UPDATED = "EVIDENCE_NODE_UPDATED"
    INTAKE_SAVED = "INTAKE_SAVED"
    PRIVILEGE_ALERT = "PRIVILEGE_ALERT"
    GROUNDING_REFUSED = "GROUNDING_REFUSED"
    PRODUCTION_BLOCKED = "PRODUCTION_BLOCKED"
    EXAMINATION_SAVED = "EXAMINATION_SAVED"
    PETITION_SAVED = "PETITION_SAVED"
    DASHBOARD_UPDATED = "DASHBOARD_UPDATED"
    OTHER = "OTHER"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _event_id(when: Optional[datetime] = None) -> str:
    dt = when or datetime.now(timezone.utc)
    # EVT-YYYYMMDD-###### sequential-looking suffix
    return f"EVT-{dt.strftime('%Y%m%d')}-{uuid4().int % 1_000_000:06d}"


@dataclass
class AuditActor:
    type: ActorType = ActorType.SYSTEM
    model: Optional[str] = None  # e.g. ALA-v0.4.2
    layer: Optional[str] = None  # e.g. EVIDENCE_MATRIX
    user_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"type": self.type.value}
        if self.model:
            d["model"] = self.model
        if self.layer:
            d["layer"] = self.layer
        if self.user_id:
            d["user_id"] = self.user_id
        return d

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "AuditActor":
        return AuditActor(
            type=ActorType(data.get("type", ActorType.SYSTEM.value)),
            model=data.get("model"),
            layer=data.get("layer"),
            user_id=data.get("user_id"),
        )

    @staticmethod
    def ai_engine(
        *,
        model: str = "ALA-v0.4.2",
        layer: str = "EVIDENCE_MATRIX",
    ) -> "AuditActor":
        return AuditActor(type=ActorType.AI_ENGINE, model=model, layer=layer)


@dataclass
class ChainOfCustodySnapshot:
    document_hash: str = ""
    ingestion_method: str = "client_upload"
    upload_timestamp: Optional[str] = None
    original_filename: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_hash": self.document_hash,
            "ingestion_method": self.ingestion_method,
            "upload_timestamp": self.upload_timestamp,
            "original_filename": self.original_filename,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "ChainOfCustodySnapshot":
        return ChainOfCustodySnapshot(
            document_hash=str(data.get("document_hash") or ""),
            ingestion_method=str(data.get("ingestion_method") or "client_upload"),
            upload_timestamp=data.get("upload_timestamp"),
            original_filename=data.get("original_filename"),
        )


@dataclass
class EvidenceNodeCreatedDetails:
    node_id: str
    source_document: str = ""
    source_location: str = ""  # e.g. page_23_line_1140
    extracted_facts: list[str] = field(default_factory=list)
    auto_tagged_categories: list[str] = field(default_factory=list)
    confidence_score: float = 0.0
    human_verified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "source_document": self.source_document,
            "source_location": self.source_location,
            "extracted_facts": list(self.extracted_facts),
            "auto_tagged_categories": list(self.auto_tagged_categories),
            "confidence_score": self.confidence_score,
            "human_verified": self.human_verified,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "EvidenceNodeCreatedDetails":
        return EvidenceNodeCreatedDetails(
            node_id=str(data.get("node_id") or ""),
            source_document=str(data.get("source_document") or ""),
            source_location=str(data.get("source_location") or ""),
            extracted_facts=list(data.get("extracted_facts") or []),
            auto_tagged_categories=list(data.get("auto_tagged_categories") or []),
            confidence_score=float(data.get("confidence_score") or 0.0),
            human_verified=bool(data.get("human_verified", False)),
        )


@dataclass
class AuditEvent:
    """
    Single append-only audit record.

    Matches workbench JSON shape (event_id, actor, action, details, chain_of_custody).
    """

    event_id: str = field(default_factory=_event_id)
    timestamp: str = field(default_factory=_utcnow_iso)
    actor: AuditActor = field(default_factory=AuditActor)
    action: AuditAction = AuditAction.OTHER
    details: dict[str, Any] = field(default_factory=dict)
    chain_of_custody: Optional[ChainOfCustodySnapshot] = None
    matter_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "actor": self.actor.to_dict(),
            "action": self.action.value,
            "details": dict(self.details),
        }
        if self.chain_of_custody is not None:
            d["chain_of_custody"] = self.chain_of_custody.to_dict()
        if self.matter_id:
            d["matter_id"] = self.matter_id
        return d

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "AuditEvent":
        coc = data.get("chain_of_custody")
        action = data.get("action", AuditAction.OTHER.value)
        return AuditEvent(
            event_id=str(data.get("event_id") or _event_id()),
            timestamp=str(data.get("timestamp") or _utcnow_iso()),
            actor=AuditActor.from_dict(data.get("actor") or {}),
            action=AuditAction(action) if not isinstance(action, AuditAction) else action,
            details=dict(data.get("details") or {}),
            chain_of_custody=(
                ChainOfCustodySnapshot.from_dict(coc) if coc else None
            ),
            matter_id=data.get("matter_id"),
        )

    @staticmethod
    def evidence_node_created(
        *,
        node_id: str,
        source_document: str,
        source_location: str = "",
        extracted_facts: Optional[list[str]] = None,
        auto_tagged_categories: Optional[list[str]] = None,
        confidence_score: float = 0.0,
        human_verified: bool = False,
        document_hash: str = "",
        ingestion_method: str = "client_upload",
        upload_timestamp: Optional[str] = None,
        original_filename: Optional[str] = None,
        matter_id: Optional[str] = None,
        model: str = "ALA-v0.4.2",
        layer: str = "EVIDENCE_MATRIX",
        timestamp: Optional[str] = None,
    ) -> "AuditEvent":
        details = EvidenceNodeCreatedDetails(
            node_id=node_id,
            source_document=source_document,
            source_location=source_location,
            extracted_facts=list(extracted_facts or []),
            auto_tagged_categories=list(auto_tagged_categories or []),
            confidence_score=confidence_score,
            human_verified=human_verified,
        )
        # Fixed example shape support: EVT-20260718-002847 style when timestamp given
        ts = timestamp or _utcnow_iso()
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            eid = f"EVT-{dt.strftime('%Y%m%d')}-{uuid4().int % 1_000_000:06d}"
        except ValueError:
            eid = _event_id()
            dt = None

        return AuditEvent(
            event_id=eid,
            timestamp=ts,
            actor=AuditActor.ai_engine(model=model, layer=layer),
            action=AuditAction.EVIDENCE_NODE_CREATED,
            details=details.to_dict(),
            chain_of_custody=ChainOfCustodySnapshot(
                document_hash=document_hash
                if document_hash.startswith("sha256:") or not document_hash
                else f"sha256:{document_hash}",
                ingestion_method=ingestion_method,
                upload_timestamp=upload_timestamp,
                original_filename=original_filename,
            ),
            matter_id=matter_id,
        )
