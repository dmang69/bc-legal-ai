"""
Layer 1 ingestion domain module (skeleton; modular monolith worker-friendly).

Pipeline:
  classify → metadata extract → hash dedup / near-dup →
  (optional) transcription → confidence + HITL → EvidenceNode draft

Does not quote statute text. No model weights required for this skeleton.
Not legal advice. Do not upload confidential files to public demos.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from architecture.evidence_node import (
    CustodySpan,
    EvidenceNode,
    KeyFact,
    PrivilegeClass,
)
from services.classifier.service import ClassificationResult, classify_document
from services.common.confidence import ConfidenceScore, HitlDecision, score_confidence
from services.transcription.service import TranscriptionResult, transcribe_audio_stub


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class ExtractedMetadata:
    date_created: Optional[str] = None
    date_received: Optional[str] = None
    sender: Optional[str] = None
    recipients: list[str] = field(default_factory=list)
    subject: Optional[str] = None
    chain_of_custody: list[CustodySpan] = field(default_factory=list)
    confidence: float = 0.0
    missing_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "date_created": self.date_created,
            "date_received": self.date_received,
            "sender": self.sender,
            "recipients": list(self.recipients),
            "subject": self.subject,
            "chain_of_custody": [c.to_dict() for c in self.chain_of_custody],
            "confidence": self.confidence,
            "missing_fields": list(self.missing_fields),
        }


@dataclass
class DedupResult:
    is_exact_duplicate: bool = False
    duplicate_of_hash: Optional[str] = None
    near_duplicates: list[str] = field(default_factory=list)  # hashes
    similarity_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "is_exact_duplicate": self.is_exact_duplicate,
            "duplicate_of_hash": self.duplicate_of_hash,
            "near_duplicates": list(self.near_duplicates),
            "similarity_notes": list(self.similarity_notes),
        }


@dataclass
class IngestRequest:
    filename: str
    data: bytes
    matter_id: str
    text_hint: str = ""
    mime_hint: Optional[str] = None
    custodian: str = "unknown"
    known_hashes: Optional[set[str]] = None  # bare hex
    known_text_fingerprints: Optional[dict[str, str]] = None  # hash -> fingerprint
    privilege_class: PrivilegeClass = PrivilegeClass.OPEN
    object_store_uri: Optional[str] = None


@dataclass
class IngestResult:
    doc_hash: str
    classification: ClassificationResult
    metadata: ExtractedMetadata
    dedup: DedupResult
    confidence: ConfidenceScore
    hitl: HitlDecision
    node_draft: Optional[EvidenceNode] = None
    transcription: Optional[TranscriptionResult] = None
    status: str = "PENDING_HITL"  # ACCEPTED | PENDING_HITL | DUPLICATE | REJECTED

    def to_dict(self) -> dict:
        return {
            "doc_hash": self.doc_hash,
            "classification": self.classification.to_dict(),
            "metadata": self.metadata.to_dict(),
            "dedup": self.dedup.to_dict(),
            "confidence": self.confidence.to_dict(),
            "hitl": self.hitl.to_dict(),
            "node_draft": self.node_draft.to_dict() if self.node_draft else None,
            "transcription": self.transcription.to_dict() if self.transcription else None,
            "status": self.status,
        }


_DATE_RE = re.compile(
    r"\b(20\d{2}-\d{2}-\d{2})\b|"
    r"\b((?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+20\d{2})\b",
    re.I,
)
_FROM_RE = re.compile(r"^from:\s*(.+)$", re.I | re.M)
_TO_RE = re.compile(r"^to:\s*(.+)$", re.I | re.M)
_SUBJ_RE = re.compile(r"^subject:\s*(.+)$", re.I | re.M)


def extract_metadata(
    *,
    filename: str,
    text: str,
    custodian: str,
) -> ExtractedMetadata:
    """Heuristic metadata + chain-of-custody seed span."""
    dates = [m.group(0) for m in _DATE_RE.finditer(text or "")]
    sender_m = _FROM_RE.search(text or "")
    to_m = _TO_RE.search(text or "")
    subj_m = _SUBJ_RE.search(text or "")
    sender = sender_m.group(1).strip() if sender_m else None
    recipients = [to_m.group(1).strip()] if to_m else []
    subject = subj_m.group(1).strip() if subj_m else None
    date_created = dates[0] if dates else None

    missing: list[str] = []
    conf = 0.5
    if date_created:
        conf += 0.15
    else:
        missing.append("date_created")
    if sender:
        conf += 0.15
    else:
        missing.append("sender")
    if not text.strip():
        missing.append("extracted_text")
        conf -= 0.2

    custody = [
        CustodySpan(
            holder=custodian or "unknown",
            from_date=_utcnow()[:10],
            to_date=None,
            method="user_upload",
        )
    ]
    return ExtractedMetadata(
        date_created=date_created,
        date_received=_utcnow()[:10],
        sender=sender,
        recipients=recipients,
        subject=subject,
        chain_of_custody=custody,
        confidence=max(0.0, min(1.0, conf)),
        missing_fields=missing,
    )


def _text_fingerprint(text: str) -> str:
    """Normalize whitespace for cheap near-duplicate detection."""
    norm = re.sub(r"\s+", " ", (text or "").lower()).strip()
    if len(norm) < 40:
        return ""
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def check_dedup(
    bare_hash: str,
    text: str,
    known_hashes: Optional[set[str]],
    known_fps: Optional[dict[str, str]],
) -> DedupResult:
    known_hashes = known_hashes or set()
    known_fps = known_fps or {}
    result = DedupResult()
    if bare_hash in known_hashes:
        result.is_exact_duplicate = True
        result.duplicate_of_hash = f"sha256:{bare_hash}"
        result.similarity_notes.append("exact_sha256_match")
        return result
    fp = _text_fingerprint(text)
    if fp:
        for h, other_fp in known_fps.items():
            if other_fp == fp and h != bare_hash:
                result.near_duplicates.append(f"sha256:{h}")
                result.similarity_notes.append("normalized_text_fingerprint_match")
    return result


def _privilege_signal(text: str, filename: str) -> bool:
    blob = f"{filename} {text}".lower()
    keys = (
        "solicitor-client",
        "solicitor–client",
        "privileged",
        "without prejudice",
        "legal advice",
        "attorney-client",
    )
    return any(k in blob for k in keys)


def ingest_document(req: IngestRequest) -> IngestResult:
    """Run Layer 1 pipeline; emit EvidenceNode draft + HITL decision."""
    bare = _sha256(req.data)
    doc_hash = f"sha256:{bare}"
    text = req.text_hint or ""

    classification = classify_document(
        filename=req.filename, text=text, mime_hint=req.mime_hint
    )

    transcription: Optional[TranscriptionResult] = None
    tx_conf: Optional[float] = None
    if classification.label.value in ("AUDIO", "VIDEO"):
        transcription = transcribe_audio_stub(req.data, filename=req.filename)
        tx_conf = transcription.confidence
        if transcription.full_text:
            text = (text + "\n" + transcription.full_text).strip()

    metadata = extract_metadata(
        filename=req.filename, text=text, custodian=req.custodian
    )
    dedup = check_dedup(bare, text, req.known_hashes, req.known_text_fingerprints)

    if dedup.is_exact_duplicate:
        conf, hitl = score_confidence(
            classification=classification.confidence,
            extraction=metadata.confidence,
            transcription=tx_conf,
            privilege_signal=_privilege_signal(text, req.filename),
            near_duplicate=False,
            missing_metadata=bool(metadata.missing_fields),
        )
        return IngestResult(
            doc_hash=doc_hash,
            classification=classification,
            metadata=metadata,
            dedup=dedup,
            confidence=conf,
            hitl=hitl,
            node_draft=None,
            transcription=transcription,
            status="DUPLICATE",
        )

    conf, hitl = score_confidence(
        classification=classification.confidence,
        extraction=metadata.confidence,
        transcription=tx_conf,
        privilege_signal=_privilege_signal(text, req.filename)
        or req.privilege_class
        in (PrivilegeClass.PROTECTED, PrivilegeClass.RESTRICTED),
        near_duplicate=bool(dedup.near_duplicates),
        missing_metadata=bool(metadata.missing_fields),
    )

    # Draft node id — production uses sequential allocator
    short = bare[:6]
    node = EvidenceNode(
        node_id=f"EV-{datetime.now(timezone.utc).year}-{int(short, 16) % 1_000_000:06d}",
        doc_hash=doc_hash,
        privilege_class=req.privilege_class,
        source_type=classification.source_type,
        date_created=metadata.date_created,
        date_received=metadata.date_received,
        custodian=req.custodian,
        extracted_text=text[:50_000],
        chain_of_custody=list(metadata.chain_of_custody),
        matter_id=req.matter_id,
        source_file=req.filename,
        key_facts=[],
    )
    if metadata.sender:
        node.key_facts.append(
            KeyFact(fact=f"sender={metadata.sender}", confidence=metadata.confidence, fact_key="sender")
        )

    status = "PENDING_HITL" if hitl.required else "ACCEPTED"
    return IngestResult(
        doc_hash=doc_hash,
        classification=classification,
        metadata=metadata,
        dedup=dedup,
        confidence=conf,
        hitl=hitl,
        node_draft=node,
        transcription=transcription,
        status=status,
    )
