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

from architecture.privilege_schemas import PartyCommRole, PrivilegeBasis, PrivilegeStatus
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
    if any(low.endswith(ext) for ext in (".mp3", ".wav", ".m4a", ".ogg")):
        return EvidenceType.AUDIO
    if any(low.endswith(ext) for ext in (".mp4", ".mov", ".webm")):
        return EvidenceType.VIDEO_FRAME
    if "transcript" in low or low.endswith(".vtt") or low.endswith(".srt"):
        return EvidenceType.TRANSCRIPT
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
    chain_of_custody_detail: str = "user_upload",
    date_captured: Optional[str] = None,
    privilege_owner: Optional[str] = None,
    is_client_lawyer_comm: bool = False,
    actor_id: str = "system",
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

    p_state = PrivilegeStatus.UNCLAIMED
    p_basis = PrivilegeBasis.NONE
    p_lock = False

    if privilege_owner and is_client_lawyer_comm:
        proposal = propose_privilege_tag(
            sender_role=PartyCommRole.CLIENT,
            recipient_role=PartyCommRole.LAWYER,
            advice_sought=True,
            advice_given=False,
            litigation_context=True,
            confidence=0.5,
        )
        p_basis = proposal.proposed_basis
        if p_basis != PrivilegeBasis.NONE:
            p_state = PrivilegeStatus.CLAIMED
            p_lock = True  # cannot export without privilege gate
            human_notes = (
                (human_notes + " " if human_notes else "")
                + f"[privilege_proposal conf={proposal.confidence:.2f} "
                f"review={proposal.requires_human_review} owner={privilege_owner}]"
            )

    item = EvidenceItem(
        source_file=safe_name,
        matter_id=matrix.matter_id,
        evidence_type=_guess_type(safe_name, human_notes),
        file_hash=digest,
        privilege_state=p_state,
        privilege_basis=p_basis,
        privilege_lock=p_lock,
        date_captured=captured,
        date_received=_utcnow(),
        parties_referenced=list(parties or []),
        location_referenced=location,
        claim_tags=tags,
        ocr_confidence=0.0,
        human_notes=human_notes,
        admissibility_flag=AdmissibilityFlag.NEEDS_VERIFICATION,
        chain_of_custody=[],
    )
    item.append_custody(
        "ingested",
        actor_id=actor_id,
        detail=chain_of_custody_detail,
        timestamp=item.date_received,
    )
    item.append_custody(
        "hash_recorded",
        actor_id=actor_id,
        detail=f"sha256={digest}",
        timestamp=item.date_received,
    )
    matrix.add(item)
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
    notes = kwargs.pop("human_notes", text[:500])
    item = ingest_bytes(matrix, filename=filename, data=data, human_notes=notes, **kwargs)
    matrix.ensure_dirs()
    prefix = (item.file_hash or "unknown")[:16]
    derived = matrix.derived_dir / f"{prefix}_{Path(filename).name}.txt"
    derived.write_text(text, encoding="utf-8")
    item.append_custody("derived_text_written", detail=str(derived.name))
    if not item.claim_tags:
        item.claim_tags = suggest_claim_tags(text)
    matrix.add(item)
    return item
