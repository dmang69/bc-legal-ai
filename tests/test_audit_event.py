"""Audit event EVIDENCE_NODE_CREATED shape and emission."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.audit_event import AuditAction, AuditEvent
from backend.matters import create_matter


def test_evidence_node_created_shape():
    ev = AuditEvent.evidence_node_created(
        node_id="EM-062",
        source_document="transcript_910222034.pdf",
        source_location="page_23_line_1140",
        extracted_facts=[
            "Notice dated November 12, 2025",
            "Sent by registered mail",
            "Delivered November 17, 2025",
        ],
        auto_tagged_categories=["notice", "service", "timeline"],
        confidence_score=0.97,
        human_verified=False,
        document_hash="sha256:a1b2c3d4e5f6",
        ingestion_method="client_upload",
        upload_timestamp="2026-07-15T14:22:00-08:00",
        original_filename="rtb_transcript.pdf",
        matter_id="demo",
        timestamp="2026-07-18T22:23:14-08:00",
    )
    d = ev.to_dict()
    assert d["event_id"].startswith("EVT-20260718-")
    assert d["timestamp"] == "2026-07-18T22:23:14-08:00"
    assert d["actor"]["type"] == "AI_ENGINE"
    assert d["actor"]["model"] == "ALA-v0.4.2"
    assert d["actor"]["layer"] == "EVIDENCE_MATRIX"
    assert d["action"] == "EVIDENCE_NODE_CREATED"
    assert d["details"]["node_id"] == "EM-062"
    assert d["details"]["source_location"] == "page_23_line_1140"
    assert d["details"]["confidence_score"] == 0.97
    assert d["details"]["human_verified"] is False
    assert "Notice dated November 12" in d["details"]["extracted_facts"][0]
    assert d["chain_of_custody"]["document_hash"].startswith("sha256:")
    assert d["chain_of_custody"]["original_filename"] == "rtb_transcript.pdf"
    # round-trip
    ev2 = AuditEvent.from_dict(d)
    assert ev2.action == AuditAction.EVIDENCE_NODE_CREATED


def test_ingest_emits_audit():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        s = create_matter("Audit", matter_id="m-aud", root=root)
        s.ingest_file(
            "transcript_910222034.pdf",
            b"%PDF-fake-bytes%",
            human_notes=(
                "Notice dated November 12, 2025\n"
                "Sent by registered mail\n"
                "Delivered November 17, 2025"
            ),
        )
        events = s.list_audit_events(action="EVIDENCE_NODE_CREATED")
        assert len(events) >= 1
        ev = events[-1]
        d = ev.to_dict()
        assert d["action"] == "EVIDENCE_NODE_CREATED"
        assert d["actor"]["layer"] == "EVIDENCE_MATRIX"
        assert d["details"]["node_id"].startswith("EM-")
        assert "ev_node_id" in d["details"]
        assert d["details"]["ev_node_id"].startswith("EV-")
        path = root / "m-aud" / "audit" / "events.jsonl"
        assert path.is_file()
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        last = json.loads(lines[-1])
        assert last["action"] == "EVIDENCE_NODE_CREATED"


if __name__ == "__main__":
    test_evidence_node_created_shape()
    test_ingest_emits_audit()
    print("OK: 2 audit event tests passed")
