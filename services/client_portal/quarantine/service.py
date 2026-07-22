"""
Encrypted quarantine for uploads — never write straight to searchable matter storage.

Pipeline: upload → quarantine → malware/metadata/class/privilege/provenance → index.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class UploadStatus(str, Enum):
    UPLOADED = "UPLOADED"
    QUARANTINED = "QUARANTINED"
    PROCESSING = "PROCESSING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    PRIVILEGE_REVIEW = "PRIVILEGE_REVIEW"
    CLASSIFIED = "CLASSIFIED"
    INDEXED = "INDEXED"
    LINKED_TO_EVIDENCE = "LINKED_TO_EVIDENCE"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


@dataclass
class QuarantineItem:
    upload_id: str
    matter_id: str
    filename: str
    content_hash: str
    status: UploadStatus
    document_type: str = ""
    creator: str = ""
    document_date: Optional[str] = None
    how_obtained: str = ""
    legal_advice_appears: bool = False
    encrypted_blob_ref: str = ""  # placeholder for encrypted object store key
    exif: dict[str, Any] = field(default_factory=dict)
    client_description: str = ""
    malware_clean: Optional[bool] = None
    searchable: bool = False  # never True while quarantined
    created_at: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "upload_id": self.upload_id,
            "matter_id": self.matter_id,
            "filename": self.filename,
            "content_hash": self.content_hash,
            "status": self.status.value,
            "document_type": self.document_type,
            "creator": self.creator,
            "document_date": self.document_date,
            "how_obtained": self.how_obtained,
            "legal_advice_appears": self.legal_advice_appears,
            "encrypted_blob_ref": self.encrypted_blob_ref,
            "exif": dict(self.exif),
            "client_description": self.client_description,
            "malware_clean": self.malware_clean,
            "searchable": self.searchable,
            "created_at": self.created_at,
        }


@dataclass
class QuarantineService:
    items: dict[str, QuarantineItem] = field(default_factory=dict)

    def ingest(
        self,
        *,
        matter_id: str,
        filename: str,
        data: bytes,
        document_type: str = "",
        creator: str = "",
        document_date: Optional[str] = None,
        how_obtained: str = "",
        legal_advice_appears: bool = False,
        exif: Optional[dict[str, Any]] = None,
        client_description: str = "",
    ) -> QuarantineItem:
        """Enter encrypted quarantine — not searchable matter storage."""
        digest = hashlib.sha256(data).hexdigest()
        uid = f"upl_{uuid4().hex[:12]}"
        item = QuarantineItem(
            upload_id=uid,
            matter_id=matter_id,
            filename=filename,
            content_hash=f"sha256:{digest}",
            status=UploadStatus.QUARANTINED,
            document_type=document_type,
            creator=creator,
            document_date=document_date,
            how_obtained=how_obtained,
            legal_advice_appears=legal_advice_appears,
            encrypted_blob_ref=f"quarantine/{matter_id}/{uid}",
            exif=dict(exif or {}),  # never invent EXIF
            client_description=client_description,
            searchable=False,
        )
        if legal_advice_appears:
            item.status = UploadStatus.PRIVILEGE_REVIEW
        self.items[uid] = item
        return item

    def mark_malware_result(self, upload_id: str, clean: bool) -> QuarantineItem:
        item = self.items[upload_id]
        item.malware_clean = clean
        if not clean:
            item.status = UploadStatus.REJECTED
        else:
            item.status = UploadStatus.PROCESSING
        return item

    def promote_to_indexable(self, upload_id: str) -> QuarantineItem:
        item = self.items[upload_id]
        if item.malware_clean is not True:
            raise PermissionError("Cannot index until malware clean.")
        if item.status == UploadStatus.PRIVILEGE_REVIEW:
            raise PermissionError("Privilege review required before indexing.")
        item.status = UploadStatus.INDEXED
        item.searchable = True
        return item
