"""
Privilege-preserving production gate — freeze snapshot, two independent
professional actions, signed hash-locked export manifest.

Waiver is never inferred from general AI processing consent.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from services.reasoning.hitl.approvals.records import ApprovalRegistry
from services.reasoning.hitl.privilege_check.scan import scan_pre_output


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class OutputClass(str, Enum):
    COURT_FILING = "COURT_FILING"
    TRIBUNAL_FILING = "TRIBUNAL_FILING"
    EVIDENCE_PACKAGE = "EVIDENCE_PACKAGE"
    DISCOVERY_PRODUCTION = "DISCOVERY_PRODUCTION"
    EMAIL_TO_OPPOSING_COUNSEL = "EMAIL_TO_OPPOSING_COUNSEL"
    SETTLEMENT_COMMUNICATION = "SETTLEMENT_COMMUNICATION"
    CLIENT_EXPORT = "CLIENT_EXPORT"
    PUBLIC_REPORT = "PUBLIC_REPORT"
    MODEL_PROVIDER_EXPORT = "MODEL_PROVIDER_EXPORT"


class ProductionStatus(str, Enum):
    DRAFT = "DRAFT"
    FROZEN = "FROZEN"
    BLOCKED = "BLOCKED"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    RELEASED = "RELEASED"
    INVALIDATED = "INVALIDATED"


HIGH_RISK = {
    OutputClass.COURT_FILING,
    OutputClass.TRIBUNAL_FILING,
    OutputClass.DISCOVERY_PRODUCTION,
    OutputClass.EMAIL_TO_OPPOSING_COUNSEL,
    OutputClass.MODEL_PROVIDER_EXPORT,
}


@dataclass
class ProductionFlag:
    document_id: str
    risk: str
    location: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "risk": self.risk,
            "location": self.location,
            "reason": self.reason,
        }


@dataclass
class DocumentDisposition:
    document_id: str
    disposition: str  # INCLUDE | EXCLUDE
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "disposition": self.disposition,
            "reason": self.reason,
        }


@dataclass
class ExportManifest:
    production_id: str
    matter_id: str
    output_class: str
    snapshot_hash: str
    included: list[DocumentDisposition]
    excluded: list[DocumentDisposition]
    reviewer_id: Optional[str]
    approver_id: Optional[str]
    recipient: str
    signed_at: Optional[str] = None
    signature: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "production_id": self.production_id,
            "matter_id": self.matter_id,
            "output_class": self.output_class,
            "snapshot_hash": self.snapshot_hash,
            "included": [d.to_dict() for d in self.included],
            "excluded": [d.to_dict() for d in self.excluded],
            "reviewer_id": self.reviewer_id,
            "approver_id": self.approver_id,
            "recipient": self.recipient,
            "signed_at": self.signed_at,
            "signature": self.signature,
        }

    def sign(self) -> str:
        payload = json.dumps(
            {
                "production_id": self.production_id,
                "snapshot_hash": self.snapshot_hash,
                "included": [d.to_dict() for d in self.included],
                "approver_id": self.approver_id,
            },
            sort_keys=True,
        )
        self.signature = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self.signed_at = _utcnow()
        return self.signature


@dataclass
class ProductionPackage:
    production_id: str
    matter_id: str
    output_class: OutputClass
    body: str
    document_ids: list[str]
    derivative_texts: list[str]  # summaries, chronology, captions, etc.
    recipient: str
    status: ProductionStatus = ProductionStatus.DRAFT
    snapshot_hash: str = ""
    flags: list[ProductionFlag] = field(default_factory=list)
    dispositions: list[DocumentDisposition] = field(default_factory=list)
    reviewer_id: Optional[str] = None
    approver_id: Optional[str] = None
    review_required: bool = True
    client_authorization_required: bool = False
    same_person_override: bool = False
    same_person_override_reason: str = ""
    critical_exception_open: bool = False
    competency_ok: bool = True
    redaction_valid: bool = True
    manifest: Optional[ExportManifest] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "production_id": self.production_id,
            "matter_id": self.matter_id,
            "output_class": self.output_class.value,
            "status": self.status.value,
            "snapshot_hash": self.snapshot_hash,
            "flags": [f.to_dict() for f in self.flags],
            "review_required": self.review_required,
            "client_authorization_required": self.client_authorization_required,
            "manifest": self.manifest.to_dict() if self.manifest else None,
        }


def _hash_snapshot(body: str, document_ids: list[str], derivatives: list[str]) -> str:
    raw = json.dumps(
        {"body": body, "docs": document_ids, "deriv": derivatives},
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class ProductionGate:
    packages: dict[str, ProductionPackage] = field(default_factory=dict)
    approvals: ApprovalRegistry = field(default_factory=ApprovalRegistry)

    def freeze(
        self,
        *,
        matter_id: str,
        output_class: OutputClass | str,
        body: str,
        document_ids: Optional[list[str]] = None,
        derivative_texts: Optional[list[str]] = None,
        recipient: str = "",
        critical_exception_open: bool = False,
        competency_ok: bool = True,
    ) -> ProductionPackage:
        oc = output_class if isinstance(output_class, OutputClass) else OutputClass(output_class)
        docs = list(document_ids or [])
        derivs = list(derivative_texts or [])
        pid = f"prod_{uuid4().hex[:12]}"
        snap = _hash_snapshot(body, docs, derivs)
        flags: list[ProductionFlag] = []

        # Scan primary body + derivatives (summaries, chronology, captions, notes)
        for i, text in enumerate([body] + derivs):
            scan = scan_pre_output(text)
            if not scan.clean:
                flags.append(
                    ProductionFlag(
                        document_id=docs[0] if docs else f"artifact_{i}",
                        risk="SOLICITOR_CLIENT_PRIVILEGE"
                        if scan.hits
                        else "WAIVER_RISK",
                        location=f"content_unit_{i}",
                        reason=scan.message,
                    )
                )

        dispositions = [
            DocumentDisposition(document_id=d, disposition="INCLUDE", reason="pending review")
            for d in docs
        ]
        pkg = ProductionPackage(
            production_id=pid,
            matter_id=matter_id,
            output_class=oc,
            body=body,
            document_ids=docs,
            derivative_texts=derivs,
            recipient=recipient,
            status=ProductionStatus.FROZEN,
            snapshot_hash=snap,
            flags=flags,
            dispositions=dispositions,
            review_required=True,
            client_authorization_required=oc
            in (
                OutputClass.DISCOVERY_PRODUCTION,
                OutputClass.EMAIL_TO_OPPOSING_COUNSEL,
            ),
            critical_exception_open=critical_exception_open,
            competency_ok=competency_ok,
        )
        if flags or critical_exception_open or not competency_ok:
            pkg.status = ProductionStatus.BLOCKED
        self.packages[pid] = pkg
        return pkg

    def mark_reviewed(
        self,
        production_id: str,
        *,
        reviewer_id: str,
        dispositions: Optional[list[DocumentDisposition]] = None,
        notes: str = "",
    ) -> ProductionPackage:
        pkg = self.packages[production_id]
        if pkg.status not in (ProductionStatus.FROZEN, ProductionStatus.BLOCKED, ProductionStatus.REVIEWED):
            raise ValueError(f"Cannot review from status {pkg.status}")
        # Re-validate hash
        current = _hash_snapshot(pkg.body, pkg.document_ids, pkg.derivative_texts)
        if current != pkg.snapshot_hash:
            pkg.status = ProductionStatus.INVALIDATED
            raise ValueError("Snapshot changed after freeze — approval invalidated.")
        pkg.reviewer_id = reviewer_id
        if dispositions:
            pkg.dispositions = dispositions
        pkg.status = ProductionStatus.REVIEWED
        self.approvals.add(
            matter_id=pkg.matter_id,
            production_id=production_id,
            stage="REVIEW",
            actor_id=reviewer_id,
            decision="APPROVED",
            notes=notes,
            snapshot_hash=pkg.snapshot_hash,
        )
        return pkg

    def approve(
        self,
        production_id: str,
        *,
        approver_id: str,
        notes: str = "",
        same_person_override: bool = False,
        same_person_override_reason: str = "",
        disclosure_authority: bool = True,
    ) -> ProductionPackage:
        pkg = self.packages[production_id]
        if pkg.status != ProductionStatus.REVIEWED:
            raise ValueError("Must complete independent review before approval.")
        current = _hash_snapshot(pkg.body, pkg.document_ids, pkg.derivative_texts)
        if current != pkg.snapshot_hash:
            pkg.status = ProductionStatus.INVALIDATED
            raise ValueError("Output changed after approval window — re-freeze required.")

        high = pkg.output_class in HIGH_RISK
        if high and pkg.reviewer_id == approver_id and not same_person_override:
            raise ValueError(
                "High-risk productions require two independent professionals "
                "(or documented same-person override)."
            )
        if same_person_override and not same_person_override_reason.strip():
            raise ValueError("Same-person override requires a written reason.")

        # Hard blocks
        if pkg.critical_exception_open:
            pkg.status = ProductionStatus.BLOCKED
            raise PermissionError("Critical exception open — release prohibited.")
        if not pkg.competency_ok:
            raise PermissionError("Approving lawyer failed competency gate.")
        if not disclosure_authority:
            raise PermissionError("Disclosure authority missing.")
        if not pkg.redaction_valid:
            raise PermissionError("Redaction validation failed.")
        if any(f.risk for f in pkg.flags) and not notes:
            # still allow if reviewer disposition excluded them
            excluded_ids = {
                d.document_id for d in pkg.dispositions if d.disposition == "EXCLUDE"
            }
            unresolved = [f for f in pkg.flags if f.document_id not in excluded_ids]
            if unresolved:
                pkg.status = ProductionStatus.BLOCKED
                raise PermissionError("Unresolved privilege flags — exclude or clear.")

        pkg.approver_id = approver_id
        pkg.same_person_override = same_person_override
        pkg.same_person_override_reason = same_person_override_reason
        included = [d for d in pkg.dispositions if d.disposition == "INCLUDE"]
        excluded = [d for d in pkg.dispositions if d.disposition == "EXCLUDE"]
        for d in excluded:
            if not d.reason:
                d.reason = "Excluded by reviewer"
        manifest = ExportManifest(
            production_id=production_id,
            matter_id=pkg.matter_id,
            output_class=pkg.output_class.value,
            snapshot_hash=pkg.snapshot_hash,
            included=included,
            excluded=excluded,
            reviewer_id=pkg.reviewer_id,
            approver_id=approver_id,
            recipient=pkg.recipient,
        )
        manifest.sign()
        pkg.manifest = manifest
        pkg.status = ProductionStatus.APPROVED
        self.approvals.add(
            matter_id=pkg.matter_id,
            production_id=production_id,
            stage="APPROVE",
            actor_id=approver_id,
            decision="APPROVED",
            notes=notes,
            snapshot_hash=pkg.snapshot_hash,
        )
        return pkg

    def release(self, production_id: str) -> ProductionPackage:
        pkg = self.packages[production_id]
        if pkg.status != ProductionStatus.APPROVED or not pkg.manifest:
            raise PermissionError("Release requires signed approved manifest.")
        current = _hash_snapshot(pkg.body, pkg.document_ids, pkg.derivative_texts)
        if current != pkg.snapshot_hash:
            pkg.status = ProductionStatus.INVALIDATED
            raise PermissionError("Post-approval hash validation failed.")
        pkg.status = ProductionStatus.RELEASED
        return pkg
