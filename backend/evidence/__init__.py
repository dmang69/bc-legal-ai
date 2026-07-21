"""Evidence Matrix — Layer 2 factual backbone."""

from backend.evidence.crossref import (
    build_chronology,
    detect_corroboration_candidates,
    detect_temporal_conflicts,
    suggest_claim_tags,
)
from backend.evidence.ingest import ingest_bytes, ingest_text_record
from backend.evidence.matrix import EvidenceMatrix

__all__ = [
    "EvidenceMatrix",
    "build_chronology",
    "detect_corroboration_candidates",
    "detect_temporal_conflicts",
    "ingest_bytes",
    "ingest_text_record",
    "suggest_claim_tags",
]
