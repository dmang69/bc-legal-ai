"""Evidence Matrix — matter isolation, chronology, gaps, cross-ref."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.schemas import EvidenceItem, EvidenceType
from backend.evidence.crossref import (
    build_chronology,
    detect_corroboration_candidates,
    detect_temporal_conflicts,
    format_chronology_markdown,
    suggest_claim_tags,
)
from backend.evidence.ingest import ingest_bytes, ingest_text_record
from backend.evidence.matrix import EvidenceMatrix, MatterScopeError


def test_matter_isolation_and_persist():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        m1 = EvidenceMatrix("matter-alpha", root=root)
        m2 = EvidenceMatrix("matter-beta", root=root)
        a = EvidenceItem(
            source_file="mold.jpg",
            evidence_type=EvidenceType.PHOTO,
            claim_tags=["mold_hazard"],
            date_captured="2025-11-28",
        )
        m1.add(a)
        assert m2.get(a.id) is None
        assert m2.all() == []
        # reload
        m1b = EvidenceMatrix("matter-alpha", root=root)
        assert m1b.get(a.id) is not None
        assert m1b.get(a.id).claim_tags == ["mold_hazard"]


def test_cross_matter_add_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        m = EvidenceMatrix("m1", root=root)
        bad = EvidenceItem(source_file="x.pdf", matter_id="other-matter")
        try:
            m.add(bad)
            raised = False
        except MatterScopeError:
            raised = True
        assert raised


def test_gaps_corroboration_contradiction():
    with tempfile.TemporaryDirectory() as tmp:
        m = EvidenceMatrix("m-gaps", root=Path(tmp))
        e1 = EvidenceItem(
            source_file="20251128_photo.jpg",
            claim_tags=["mold_hazard"],
            date_captured="2025-11-28",
            location_referenced="990A",
        )
        e2 = EvidenceItem(
            source_file="city_fine.jpg",
            claim_tags=["mold_hazard", "city_enforcement"],
            date_captured="2025-11-15",
            location_referenced="990A",
        )
        m.add(e1, persist=False)
        m.add(e2, persist=False)
        assert m.gap_report(["mold_hazard", "retaliatory_eviction"]) == ["retaliatory_eviction"]
        m.link_corroborates(e1.id, e2.id, persist=False)
        assert e2.id in m.get(e1.id).corroborates
        m.link_contradicts(e1.id, e2.id, persist=False)
        assert e1.id in m.get(e2.id).contradicts
        cands = detect_corroboration_candidates(m.all())
        assert any(e1.id in pair and e2.id in pair for pair in [(a, b) for a, b, _ in cands])


def test_chronology_filename_and_iso():
    items = [
        EvidenceItem(source_file="lease_2016.jpg", date_captured="2016-03-01", claim_tags=[]),
        EvidenceItem(source_file="20251128_084839.jpg", claim_tags=["mold_hazard"]),
        EvidenceItem(source_file="undated.pdf", claim_tags=[]),
    ]
    chrono = build_chronology(items)
    assert chrono[0].sort_date == "2016-03-01"
    assert chrono[1].sort_date == "2025-11-28"
    assert chrono[2].sort_date is None
    md = format_chronology_markdown(items)
    assert "2016-03-01" in md


def test_temporal_conflict_heuristic():
    items = [
        EvidenceItem(
            source_file="a.jpg",
            date_captured="2023-06-01",
            claim_tags=["mold_hazard"],
            human_notes="landlord said fixed",
        ),
        EvidenceItem(
            source_file="b.jpg",
            date_captured="2025-11-28",
            claim_tags=["mold_hazard"],
            human_notes="ongoing mold",
        ),
    ]
    conflicts = detect_temporal_conflicts(items)
    assert len(conflicts) >= 1
    assert conflicts[0].claim_tag == "mold_hazard"


def test_ingest_preserves_hash():
    with tempfile.TemporaryDirectory() as tmp:
        m = EvidenceMatrix("m-ingest", root=Path(tmp))
        payload = b"%PDF-fake-mold-photo-bytes%"
        item = ingest_bytes(
            m,
            filename="20251128_mold.jpg",
            data=payload,
            human_notes="back unit mold",
            location="990A",
        )
        assert item.file_hash is not None
        assert len(item.file_hash) == 64
        assert item.file_hash == item.content_sha256  # alias
        assert item.evidence_id == item.id
        assert item.privilege_state.value == "UNCLAIMED"
        assert item.privilege_lock is False
        assert isinstance(item.chain_of_custody, list)
        assert any(e.get("action") == "ingested" for e in item.chain_of_custody)
        originals = list(m.originals_dir.iterdir())
        assert len(originals) == 1
        assert originals[0].read_bytes() == payload
        assert "mold_hazard" in item.claim_tags or "mold" in item.human_notes.lower()


def test_privilege_lock_blocks_export_gate():
    from architecture.privilege_schemas import PrivilegeStatus
    from backend.privilege.production_gate import export_items_from_evidence, run_production_gate

    with tempfile.TemporaryDirectory() as tmp:
        m = EvidenceMatrix("m-priv", root=Path(tmp))
        item = ingest_bytes(
            m,
            filename="advice_email.eml",
            data=b"client to lawyer advice",
            is_client_lawyer_comm=True,
            privilege_owner="client-1",
        )
        assert item.privilege_lock is True
        assert item.privilege_state == PrivilegeStatus.CLAIMED
        assert item.requires_privilege_gate() is True
        decision = run_production_gate(
            export_items_from_evidence([item]),
            destination="opposing",
        )
        assert decision.allowed is False
        assert item.evidence_id in decision.blocked_document_ids


def test_suggest_claim_tags():
    tags = suggest_claim_tags("There is black mould and the landlord failed to repair.")
    assert "mold_hazard" in tags
    assert "non_repair" in tags


def test_ingest_text_and_summary():
    with tempfile.TemporaryDirectory() as tmp:
        m = EvidenceMatrix("m-text", root=Path(tmp))
        ingest_text_record(
            m,
            filename="email_thread.txt",
            text="Email to landlord requesting mold repair after RTB order.",
        )
        s = m.summary()
        assert s["count"] == 1
        assert s["matter_id"] == "m-text"


if __name__ == "__main__":
    test_matter_isolation_and_persist()
    test_cross_matter_add_rejected()
    test_gaps_corroboration_contradiction()
    test_chronology_filename_and_iso()
    test_temporal_conflict_heuristic()
    test_ingest_preserves_hash()
    test_privilege_lock_blocks_export_gate()
    test_suggest_claim_tags()
    test_ingest_text_and_summary()
    print("OK: 9 evidence matrix tests passed")
