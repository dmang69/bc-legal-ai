"""Court/export manifest gate combining privilege, citation, and human approval checks."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from architecture.privilege_schemas import PrivilegeBasis, PrivilegeMetadata, PrivilegeStatus
from backend.api.public_demo import reject_if_public_demo
from backend.db import get_connection, init_db
from backend.identity import AuthError, UserInfo, get_identity_service
from backend.platform.citations import list_citation_audit
from backend.privilege.production_gate import ExportItem, run_production_gate


@dataclass(frozen=True)
class ExportApprovals:
    human_confirmed_facts: bool = False
    citation_reviewed: bool = False
    privilege_reviewed: bool = False
    lawyer_approved: bool = False
    client_waiver_signed: bool = False

    def to_dict(self) -> dict[str, bool]:
        return asdict(self)


@dataclass(frozen=True)
class ExportManifestResult:
    manifest_id: str
    matter_id: str
    destination: str
    status: str
    court_ready: bool
    document_ids: list[str]
    citation_ids: list[str]
    blockers: list[str] = field(default_factory=list)
    privilege_decision: dict[str, Any] = field(default_factory=dict)
    approvals: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _document_export_items(matter_id: str, document_ids: list[str]) -> tuple[list[ExportItem], list[str]]:
    blockers: list[str] = []
    items: list[ExportItem] = []
    if not document_ids:
        blockers.append("No documents selected for export")
        return items, blockers
    placeholders = ",".join("?" for _ in document_ids)
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT document_id, privilege_class, quarantine_status
            FROM documents
            WHERE matter_id = ? AND document_id IN ({placeholders})
            """,
            (matter_id, *document_ids),
        ).fetchall()
    found = {row["document_id"] for row in rows}
    missing = [doc_id for doc_id in document_ids if doc_id not in found]
    blockers.extend(f"Document not found in matter: {doc_id}" for doc_id in missing)
    for row in rows:
        if row["quarantine_status"] != "CLEAN":
            blockers.append(f"{row['document_id']}: quarantine status is {row['quarantine_status']}")
        privilege_class = (row["privilege_class"] or "UNKNOWN").upper()
        if privilege_class in {"CLAIMED", "ASSERTED", "UPHELD"}:
            status = PrivilegeStatus(privilege_class)
            basis = PrivilegeBasis.SOLICITOR_CLIENT
            human_confirmed = False
            lock = True
        elif privilege_class == "WAIVED":
            status = PrivilegeStatus.WAIVED
            basis = PrivilegeBasis.SOLICITOR_CLIENT
            human_confirmed = True
            lock = False
        else:
            status = PrivilegeStatus.UNCLAIMED
            basis = PrivilegeBasis.NONE
            human_confirmed = privilege_class not in {"UNKNOWN", ""}
            lock = privilege_class in {"UNKNOWN", ""}
        items.append(
            ExportItem(
                document_id=row["document_id"],
                privilege=PrivilegeMetadata(
                    privilege_owner=matter_id,
                    privilege_status=status,
                    privilege_basis=basis,
                    human_confirmed=human_confirmed,
                ),
                privilege_lock=lock,
            )
        )
    return items, blockers


def _citation_blockers(matter_id: str, citation_ids: list[str], approvals: ExportApprovals) -> list[str]:
    blockers: list[str] = []
    audit = list_citation_audit(matter_id)
    by_id = {row["verification_id"]: row for row in audit}
    if not citation_ids:
        blockers.append("No citation verifications selected for export")
        return blockers
    for citation_id in citation_ids:
        row = by_id.get(citation_id)
        if not row:
            blockers.append(f"Citation verification not found in matter: {citation_id}")
            continue
        if row["status"] not in {"PROVISIONAL"}:
            blockers.append(f"{citation_id}: citation status is {row['status']}")
        if row["court_ready"]:
            blockers.append(f"{citation_id}: unexpected auto court-ready citation flag")
        if not row.get("source_hash"):
            blockers.append(f"{citation_id}: missing source hash")
    if not approvals.citation_reviewed:
        blockers.append("Citation review approval missing")
    return blockers


def create_export_manifest(
    *,
    user: UserInfo,
    matter_id: str,
    document_ids: list[str],
    citation_ids: list[str],
    destination: str = "export",
    approvals: ExportApprovals | None = None,
) -> dict[str, Any]:
    reject_if_public_demo("court-ready export manifest")
    init_db()
    if not get_identity_service().can_access_matter(user, matter_id, min_level="read"):
        raise AuthError("Matter access denied")
    approvals = approvals or ExportApprovals()
    blockers: list[str] = []
    items, document_blockers = _document_export_items(matter_id, document_ids)
    blockers.extend(document_blockers)
    privilege_decision = run_production_gate(
        items,
        instructing_lawyer_signed=approvals.lawyer_approved and approvals.privilege_reviewed,
        client_waiver_signed=approvals.client_waiver_signed,
        intended_waiver=approvals.client_waiver_signed,
        destination=destination,
    )
    if not privilege_decision.allowed:
        blockers.extend(privilege_decision.reasons)
    blockers.extend(_citation_blockers(matter_id, citation_ids, approvals))
    if not approvals.human_confirmed_facts:
        blockers.append("Human-confirmed facts approval missing")
    if not approvals.privilege_reviewed:
        blockers.append("Privilege review approval missing")
    if not approvals.lawyer_approved:
        blockers.append("Supervising lawyer approval missing")

    status = "APPROVED" if not blockers else "BLOCKED"
    court_ready = status == "APPROVED"
    manifest_id = f"exp_{uuid.uuid4().hex[:12]}"
    result = ExportManifestResult(
        manifest_id=manifest_id,
        matter_id=matter_id,
        destination=destination,
        status=status,
        court_ready=court_ready,
        document_ids=document_ids,
        citation_ids=citation_ids,
        blockers=blockers,
        privilege_decision=privilege_decision.to_dict(),
        approvals=approvals.to_dict(),
    )
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO export_manifests
            (manifest_id, matter_id, destination, document_ids_json, citation_ids_json,
             status, court_ready, privilege_decision_json, blockers_json, approvals_json, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                manifest_id,
                matter_id,
                destination,
                json.dumps(document_ids),
                json.dumps(citation_ids),
                status,
                1 if court_ready else 0,
                json.dumps(result.privilege_decision),
                json.dumps(blockers),
                json.dumps(result.approvals),
                user.user_id,
            ),
        )
    return result.to_dict()


def list_export_manifests(user: UserInfo, matter_id: str) -> list[dict[str, Any]]:
    init_db()
    if not get_identity_service().can_access_matter(user, matter_id, min_level="read"):
        raise AuthError("Matter access denied")
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM export_manifests
            WHERE matter_id = ?
            ORDER BY created_at DESC
            """,
            (matter_id,),
        ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["document_ids"] = json.loads(item.pop("document_ids_json") or "[]")
        item["citation_ids"] = json.loads(item.pop("citation_ids_json") or "[]")
        item["blockers"] = json.loads(item.pop("blockers_json") or "[]")
        item["approvals"] = json.loads(item.pop("approvals_json") or "{}")
        item["privilege_decision"] = json.loads(item.pop("privilege_decision_json") or "{}")
        item["court_ready"] = bool(item["court_ready"])
        out.append(item)
    return out
