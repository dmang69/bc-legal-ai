"""
Client portal (Layer 5) — MFA stub, dashboard, evidence tracker, timeline, upload status.

Not legal advice. Public demos must not host real client matters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Session:
    session_id: str
    client_id: str
    mfa_verified: bool = False
    created_at: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "client_id": self.client_id,
            "mfa_verified": self.mfa_verified,
            "created_at": self.created_at,
        }


@dataclass
class MatterSummary:
    matter_id: str
    title: str
    status: str = "open"
    next_deadline: Optional[str] = None
    evidence_count: int = 0
    consent_gaps: list[str] = field(default_factory=list)
    tasks: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "matter_id": self.matter_id,
            "title": self.title,
            "status": self.status,
            "next_deadline": self.next_deadline,
            "evidence_count": self.evidence_count,
            "consent_gaps": list(self.consent_gaps),
            "tasks": list(self.tasks),
        }


@dataclass
class EvidenceTrackerItem:
    node_id: str
    filename: str
    status: str  # uploaded | classified | hitl | accepted | rejected
    classification: str = ""
    uploaded_at: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "filename": self.filename,
            "status": self.status,
            "classification": self.classification,
            "uploaded_at": self.uploaded_at,
        }


@dataclass
class TimelinePoint:
    ts: str
    label: str
    kind: str = "event"

    def to_dict(self) -> dict[str, Any]:
        return {"ts": self.ts, "label": self.label, "kind": self.kind}


@dataclass
class UploadDraft:
    upload_id: str
    matter_id: str
    filename: str
    proposed_class: str
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "PREVIEW"  # PREVIEW | CONFIRMED | REJECTED
    preview_note: str = "Confirm classification and metadata before processing."

    def to_dict(self) -> dict[str, Any]:
        return {
            "upload_id": self.upload_id,
            "matter_id": self.matter_id,
            "filename": self.filename,
            "proposed_class": self.proposed_class,
            "metadata": dict(self.metadata),
            "status": self.status,
            "preview_note": self.preview_note,
        }


@dataclass
class ClientPortalStub:
    matters: dict[str, MatterSummary] = field(default_factory=dict)
    sessions: dict[str, Session] = field(default_factory=dict)
    evidence: dict[str, list[EvidenceTrackerItem]] = field(default_factory=dict)
    timelines: dict[str, list[TimelinePoint]] = field(default_factory=dict)
    uploads: dict[str, UploadDraft] = field(default_factory=dict)
    # i18n keys for UI (full strings live in frontend)
    supported_locales: list[str] = field(
        default_factory=lambda: ["en", "zh-Hans", "pa", "tl"]
    )

    def login_start(self, client_id: str) -> Session:
        s = Session(session_id=f"SESS-{uuid4().hex[:10]}", client_id=client_id)
        self.sessions[s.session_id] = s
        return s

    def mfa_verify(self, session_id: str, code: str) -> bool:
        """Stub: accept any 6-digit code. Wire real TOTP/SMS in production."""
        s = self.sessions.get(session_id)
        if not s or not (code and len(code) >= 6):
            return False
        s.mfa_verified = True
        return True

    def require_mfa(self, session_id: str) -> bool:
        s = self.sessions.get(session_id)
        return bool(s and s.mfa_verified)

    def list_matters(self, client_id: str) -> list[MatterSummary]:
        _ = client_id
        return list(self.matters.values())

    def upsert_matter(self, summary: MatterSummary) -> MatterSummary:
        self.matters[summary.matter_id] = summary
        return summary

    def track_evidence(self, matter_id: str, item: EvidenceTrackerItem) -> EvidenceTrackerItem:
        self.evidence.setdefault(matter_id, []).append(item)
        m = self.matters.get(matter_id)
        if m:
            m.evidence_count = len(self.evidence[matter_id])
        return item

    def timeline(self, matter_id: str) -> list[TimelinePoint]:
        return list(self.timelines.get(matter_id, []))

    def add_timeline(self, matter_id: str, point: TimelinePoint) -> None:
        self.timelines.setdefault(matter_id, []).append(point)

    def start_upload(
        self,
        *,
        matter_id: str,
        filename: str,
        proposed_class: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> UploadDraft:
        draft = UploadDraft(
            upload_id=f"UPL-{uuid4().hex[:10]}",
            matter_id=matter_id,
            filename=filename,
            proposed_class=proposed_class,
            metadata=metadata or {},
        )
        self.uploads[draft.upload_id] = draft
        return draft

    def confirm_upload(self, upload_id: str) -> Optional[UploadDraft]:
        d = self.uploads.get(upload_id)
        if not d:
            return None
        d.status = "CONFIRMED"
        return d

    def add_reminder_task(self, matter_id: str, title: str, due: str) -> dict[str, Any]:
        task = {
            "task_id": f"TSK-{uuid4().hex[:8]}",
            "title": title,
            "due": due,
            "status": "open",
            "reminder": True,
        }
        m = self.matters.get(matter_id)
        if m:
            m.tasks.append(task)
        return task
