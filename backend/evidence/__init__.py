"""Evidence Matrix — Layer 2 factual backbone + EvidenceNode graph."""

from backend.evidence.crossref import (
    build_chronology,
    detect_corroboration_candidates,
    detect_temporal_conflicts,
    format_chronology_markdown,
    suggest_claim_tags,
)
from backend.evidence.ingest import ingest_bytes, ingest_text_record
from backend.evidence.matrix import EvidenceMatrix
from backend.evidence.contradiction_engine import (
    detect_key_fact_contradictions,
)
from backend.evidence.nodes import EvidenceNodeStore, sync_items_to_nodes
from backend.evidence.gap_detection import (
    build_gap_detection_report,
    format_gap_detection_report,
)
from backend.evidence.timeline_engine import (
    build_timeline_from_nodes,
    format_timeline_markdown,
)

__all__ = [
    "EvidenceMatrix",
    "EvidenceNodeStore",
    "build_chronology",
    "build_gap_detection_report",
    "build_timeline_from_nodes",
    "detect_corroboration_candidates",
    "detect_key_fact_contradictions",
    "detect_temporal_conflicts",
    "format_chronology_markdown",
    "format_gap_detection_report",
    "format_timeline_markdown",
    "ingest_bytes",
    "ingest_text_record",
    "suggest_claim_tags",
    "sync_items_to_nodes",
]
