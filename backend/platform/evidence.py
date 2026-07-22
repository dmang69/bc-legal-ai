"""Document quarantine + Evidence Matrix persistence (M2 foundation)."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Any, Optional

from backend.audit import get_audit_ledger
from backend.db import get_connection, init_db
from backend.identity import AuthError, UserInfo, get_identity_service

_ROOT = Path(__file__).resolve().parents[2]
_BLOB = _ROOT / "data" / "object_store"


def _did() -> str:
    return f"doc_{uuid.uuid4().hex[:16]}"


def _pid() -> str:
    return f"prop_{uuid.uuid4().hex[:16]}"


class EvidenceService:
    def quarantine_upload(
        self,
        *,
        user: UserInfo,
        matter_id: str,
        filename: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        synthetic: bool = False,
    ) -> dict[str, Any]:
        idsvc = get_identity_service()
        if not idsvc.can_access_matter(user, matter_id, min_level="write"):
            raise AuthError("Matter write access denied")
        if not data:
            raise ValueError("Empty upload")
        if len(data) > 50 * 1024 * 1024:
            raise ValueError("File exceeds 50MB limit")
        sha = hashlib.sha256(data).hexdigest()
        document_id = _did()
        _BLOB.mkdir(parents=True, exist_ok=True)
        storage_path = _BLOB / user.org_id / matter_id / f"{document_id}.bin"
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.write_bytes(data)

        # Basic "scan": block executables by extension
        lower = filename.lower()
        blocked = lower.endswith((".exe", ".dll", ".bat", ".cmd", ".ps1", ".js"))
        status = "BLOCKED" if blocked else "CLEAN"

        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO documents
                (document_id, org_id, matter_id, filename, content_type, byte_size,
                 sha256, storage_uri, quarantine_status, synthetic, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    user.org_id,
                    matter_id,
                    filename,
                    content_type,
                    len(data),
                    sha,
                    str(storage_path),
                    status,
                    1 if synthetic else 0,
                    user.user_id,
                ),
            )
            # Text extraction for text-like files
            if not blocked and (
                content_type.startswith("text/")
                or lower.endswith((".txt", ".md", ".csv"))
            ):
                text = data.decode("utf-8", errors="replace")
                page_id = f"page_{uuid.uuid4().hex[:12]}"
                page_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
                conn.execute(
                    """
                    INSERT INTO document_pages
                    (page_id, document_id, matter_id, page_number, page_hash,
                     text_content, ocr_confidence, needs_review)
                    VALUES (?, ?, ?, 1, ?, ?, 1.0, 0)
                    """,
                    (page_id, document_id, matter_id, page_hash, text),
                )

        get_audit_ledger().append(
            actor_id=user.user_id,
            action="document.quarantine",
            org_id=user.org_id,
            matter_id=matter_id,
            resource_type="document",
            resource_id=document_id,
            detail={"filename": filename, "sha256": sha, "status": status},
        )
        return {
            "document_id": document_id,
            "filename": filename,
            "sha256": sha,
            "byte_size": len(data),
            "quarantine_status": status,
            "synthetic": synthetic,
        }

    def add_proposition(
        self,
        *,
        user: UserInfo,
        matter_id: str,
        text: str,
        document_id: Optional[str] = None,
        page_id: Optional[str] = None,
        classification: str = "UNCLASSIFIED",
        span_start: Optional[int] = None,
        span_end: Optional[int] = None,
    ) -> dict[str, Any]:
        idsvc = get_identity_service()
        if not idsvc.can_access_matter(user, matter_id, min_level="write"):
            raise AuthError("Matter write access denied")
        if document_id and not page_id:
            raise ValueError("Propositions linked to a document should include page_id for provenance")
        prop_id = _pid()
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO propositions
                (proposition_id, matter_id, document_id, page_id, span_start, span_end,
                 text, classification)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prop_id,
                    matter_id,
                    document_id,
                    page_id,
                    span_start,
                    span_end,
                    text,
                    classification,
                ),
            )
        return {
            "proposition_id": prop_id,
            "matter_id": matter_id,
            "text": text,
            "classification": classification,
            "document_id": document_id,
            "page_id": page_id,
            "provenance_ok": bool(page_id or not document_id),
        }

    def list_documents(self, user: UserInfo, matter_id: str) -> list[dict[str, Any]]:
        idsvc = get_identity_service()
        if not idsvc.can_access_matter(user, matter_id):
            raise AuthError("Matter access denied")
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT document_id, filename, quarantine_status, sha256, byte_size, synthetic
                FROM documents WHERE matter_id = ? ORDER BY created_at DESC
                """,
                (matter_id,),
            ).fetchall()
        return [dict(r) for r in rows]


_ev: Optional[EvidenceService] = None


def get_evidence_service() -> EvidenceService:
    global _ev
    init_db()
    if _ev is None:
        _ev = EvidenceService()
    return _ev
