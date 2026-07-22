"""
Document retention & purging (Layer 6) — LSBC-aligned scaffolding.

Privileged vs evidence handling; client request mechanism; secure destruction log.
Not legal advice — confirm firm policy + LSBC rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Optional
from uuid import uuid4


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RetentionPolicy:
    policy_id: str
    name: str
    # years after matter close (illustrative defaults — set firm policy)
    evidence_years: int = 7
    privileged_years: int = 10
    audit_years: int = 10
    notes: str = "Confirm with LSBC / firm retention schedule."

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "evidence_years": self.evidence_years,
            "privileged_years": self.privileged_years,
            "audit_years": self.audit_years,
            "notes": self.notes,
        }


DEFAULT_POLICY = RetentionPolicy(
    policy_id="FIRM-DEFAULT",
    name="Default firm retention (scaffold)",
)


@dataclass
class DestructionRecord:
    destruction_id: str
    matter_id: str
    object_ref: str  # node_id or object store key
    classification: str  # evidence | privileged | audit
    method: str  # secure_delete | crypto_shred
    requested_by: str
    ts: str
    status: str = "COMPLETED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "destruction_id": self.destruction_id,
            "matter_id": self.matter_id,
            "object_ref": self.object_ref,
            "classification": self.classification,
            "method": self.method,
            "requested_by": self.requested_by,
            "ts": self.ts,
            "status": self.status,
        }


@dataclass
class ClientPurgeRequest:
    request_id: str
    matter_id: str
    client_id: str
    reason: str
    status: str = "PENDING_LAWYER"  # PENDING_LAWYER | APPROVED | DENIED | DONE
    ts: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "matter_id": self.matter_id,
            "client_id": self.client_id,
            "reason": self.reason,
            "status": self.status,
            "ts": self.ts,
        }


@dataclass
class RetentionService:
    policy: RetentionPolicy = field(default_factory=lambda: DEFAULT_POLICY)
    destructions: list[DestructionRecord] = field(default_factory=list)
    client_requests: list[ClientPurgeRequest] = field(default_factory=list)
    holds: set[str] = field(default_factory=set)  # matter_ids under litigation hold

    def place_hold(self, matter_id: str) -> None:
        self.holds.add(matter_id)

    def release_hold(self, matter_id: str) -> None:
        self.holds.discard(matter_id)

    def purge_eligible(
        self,
        matter_id: str,
        *,
        closed_on: str,
        classification: str = "evidence",
        today: Optional[date] = None,
    ) -> bool:
        if matter_id in self.holds:
            return False
        try:
            closed = date.fromisoformat(closed_on[:10])
        except ValueError:
            return False
        years = (
            self.policy.privileged_years
            if classification == "privileged"
            else self.policy.evidence_years
        )
        t = today or date.today()
        return (t - closed).days >= years * 365

    def secure_destroy(
        self,
        *,
        matter_id: str,
        object_ref: str,
        classification: str,
        requested_by: str,
        method: str = "crypto_shred",
    ) -> DestructionRecord:
        if matter_id in self.holds:
            raise PermissionError("Litigation hold — destruction blocked.")
        rec = DestructionRecord(
            destruction_id=f"DEST-{uuid4().hex[:10]}",
            matter_id=matter_id,
            object_ref=object_ref,
            classification=classification,
            method=method,
            requested_by=requested_by,
            ts=_utcnow(),
        )
        self.destructions.append(rec)
        return rec

    def client_request_purge(
        self, *, matter_id: str, client_id: str, reason: str
    ) -> ClientPurgeRequest:
        req = ClientPurgeRequest(
            request_id=f"CPR-{uuid4().hex[:10]}",
            matter_id=matter_id,
            client_id=client_id,
            reason=reason,
        )
        self.client_requests.append(req)
        return req
