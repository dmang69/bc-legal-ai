"""
Ingest into evidence matrix — preserve original bytes; hash; create matrix row.

No OCR in Phase 1: text records and binary stubs only.
Privilege tagging is optional and never auto-finalized (see backend.privilege.tagger).
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from architecture.privilege_schemas import (
    PartyCommRole,
    PrivilegeBasis,
    PrivilegeMetadata,
    PrivilegeStatus,
)
from architecture.schemas import AdmissibilityFlag, EvidenceItem, EvidenceType
from backend.evidence.crossref import parse_date_hint, suggest_claim_tags
from backend.evidence.matrix import EvidenceMatrix
from backend.privilege.tagger import propose_privilege_tag


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _guess_type(filename: str, text: str = "") -> EvidenceType:
    low = (filename + " " + text).lower()
    if any(low.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".heic", ".webp")):
        return EvidenceType.PHOTO
    if "lease" in low or "tenancy agreement" in low:
        return EvidenceType.CONTRACT
    if "notice" in low or "rtb-" in low:
        return EvidenceType.NOTICE
    if "email" in low or low.endswith(".eml"):
        return EvidenceType.CORRESPONDENCE
    if "decision" in low or "order" in low or "arbitrator" in low:
        return EvidenceType.OFFICIAL_ORDER
    if "receipt" in low or "invoice" in low or "payment" in low:
        return EvidenceType.FINANCIAL
    return EvidenceType.OTHER


def ingest_bytes(
    matrix: EvidenceMatrix,
    *,
    filename: str,
    data: bytes,
    claim_tags: Optional[list[str]] = None,
    human_notes: str = "",
    parties: Optional[list[str]] = None,
    location: Optional[str] = None,
    chain_of_custody: Optional[str] = None,
    date_captured: Optional[str] = None,
    privilege_owner: Optional[str] = None,
    is_client_lawyer_comm: bool = False,
) -> EvidenceItem:
    """
    Copy original to matters/{id}/evidence/originals/, append matrix row.
    Does not modify source bytes after write.
    """
    matrix.ensure_dirs()
    digest = _sha256(data)
    safe_name = Path(filename).name
    dest = matrix.originals_dir / f"{digest[:16]}_{safe_name}"
    if not dest.exists():
        dest.write_bytes(data)

    text_for_tags = human_notes + " " + safe_name
    tags = list(claim_tags) if claim_tags is not None else suggest_claim_tags(text_for_tags)
    captured = date_captured
    if not captured:
        d = parse_date_hint(safe_name, None)
        if d:
            captured = d.isoformat()

    item = EvidenceItem(
        source_file=safe_name,
        evidence_type=_guess_type(safe_name, human_notes),
        date_captured=captured,
        date_received=_utcnow(),
        parties_referenced=list(parties or []),
        location_referenced=location,
        claim_tags=tags,
        chain_of_custody=chain_of_custody or "user_upload",
        ocr_confidence=0.0,  # no OCR yet
        human_notes=human_notes,
        admissibility_flag=AdmissibilityFlag.NEEDS_VERIFICATION,
        matter_id=matrix.matter_id,
        content_sha256=digest,
    )
    matrix.add(item)

    # Optional privilege proposal (not finalized)
    if privilege_owner and is_client_lawyer_comm:
        proposal = propose_privilege_tag(
            sender_role=PartyCommRole.CLIENT,
            recipient_role=PartyCommRole.LAWYER,
            advice_sought=True,
            advice_given=False,
            litigation_context=True,
            confidence=0.5,
        )
        # Stored only as human_notes annotation in Phase 1 (full privilege store Phase 2)
        item.human_notes = (
            (item.human_notes + " " if item.human_notes else "")
            + f"[privilege_proposal basis={proposal.proposed_basis.value} "
            f"conf={proposal.confidence:.2f} review={proposal.requires_human_review}]"
        )
        matrix.add(item)  # re-save notes
        _ = PrivilegeMetadata(
            privilege_owner=privilege_owner,
            privilege_status=PrivilegeStatus.UNCLAIMED,
            privilege_basis=proposal.proposed_basis,
            classification_confidence=proposal.confidence,
            human_confirmed=False,
        )

    return item


def ingest_text_record(
    matrix: EvidenceMatrix,
    *,
    filename: str,
    text: str,
    **kwargs,
) -> EvidenceItem:
    """Ingest a text-only derived record; also writes derived/*.txt (not as original)."""
    data = text.encode("utf-8")
    item = ingest_bytes(matrix, filename=filename, data=data, human_notes=text[:500], **kwargs)
    matrix.ensure_dirs()
    derived = matrix.derived_dir / f"{item.content_sha256[:16]}_{Path(filename).name}.txt"
    derived.write_text(text, encoding="utf-8")
    if not item.claim_tags:
        item.claim_tags = suggest_claim_tags(text)
        matrix.add(item)
    return item
