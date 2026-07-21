"""EvidenceNode sequential IDs, graph edges, privilege class."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.evidence_node import (
    AuthenticityStatus,
    EvidenceNode,
    KeyFact,
    PrivilegeClass,
    SourceType,
)
from backend.evidence.ingest import ingest_bytes
from backend.evidence.matrix import EvidenceMatrix
from backend.evidence.nodes import EvidenceNodeStore
from backend.matters import create_matter


def test_sequential_ids_immutable_format():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        store = EvidenceNodeStore("m1", root=root)
        m = EvidenceMatrix("m1", root=root)
        a = ingest_bytes(m, filename="a.jpg", data=b"aaa", human_notes="mold")
        b = ingest_bytes(m, filename="b.jpg", data=b"bbb", human_notes="repair")
        n1 = store.allocate_from_item(a, custodian="tenant")
        n2 = store.allocate_from_item(b, custodian="tenant")
        assert n1.node_id.startswith("EV-")
        assert n1.node_id < n2.node_id or int(n1.node_id[-6:]) < int(n2.node_id[-6:])
        # idempotent
        n1b = store.allocate_from_item(a, custodian="tenant")
        assert n1b.node_id == n1.node_id
        # reload
        store2 = EvidenceNodeStore("m1", root=root)
        assert store2.get(n1.node_id) is not None
        assert store2.get(n1.node_id).doc_hash.startswith("sha256:")


def test_privilege_class_protected():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        s = create_matter("Priv", matter_id="mp", root=root)
        s.ingest_file(
            "advice.eml",
            b"advice body",
            is_client_lawyer_comm=True,
            privilege_owner="client-1",
            custodian="lawyer",
        )
        nodes = s.nodes.all()
        assert len(nodes) == 1
        assert nodes[0].privilege_class == PrivilegeClass.PROTECTED
        assert nodes[0].requires_privilege_gate() is True


def test_relationships_and_key_facts():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        store = EvidenceNodeStore("m-rel", root=root)
        m = EvidenceMatrix("m-rel", root=root)
        a = ingest_bytes(
            m, filename="20251112_notice.jpg", data=b"1", human_notes="eviction notice"
        )
        b = ingest_bytes(
            m, filename="20251117_email.txt", data=b"2", human_notes="same notice discussed"
        )
        n1 = store.allocate_from_item(a, custodian="tenant", persist=False)
        n2 = store.allocate_from_item(b, custodian="tenant", persist=False)
        store.link_corroborates(n1.node_id, n2.node_id, persist=False)
        store.set_temporal(n1.node_id, n2.node_id, persist=False)
        store.add_key_fact(
            n1.node_id,
            "Eviction notice served on tenant",
            confidence=0.98,
            source_span="para_3_lines_11-14",
            persist=True,
        )
        n1 = store.get(n1.node_id)
        assert n2.node_id in n1.corroborates
        assert n2.node_id in n1.temporal_sequence.after
        assert n1.key_facts[0].fact.startswith("Eviction")


def test_example_shape_matches_spec():
    """Sanity: serialized shape has required top-level keys."""
    node = EvidenceNode(
        node_id="EV-2026-000147",
        doc_hash="sha256:9f2a",
        privilege_class=PrivilegeClass.PROTECTED,
        source_type=SourceType.PHOTO,
        date_created="2025-11-12T00:00:00-08:00",
        date_received="2025-11-17T14:22:00-08:00",
        custodian="tenant",
        authenticity_status=AuthenticityStatus.UNVERIFIED,
        key_facts=[
            KeyFact(
                fact="Eviction notice served on tenant",
                confidence=0.98,
                source_span="para_3_lines_11-14",
            )
        ],
    )
    d = node.to_dict()
    for key in (
        "node_id",
        "doc_hash",
        "privilege_class",
        "source_type",
        "date_created",
        "date_received",
        "date_entered_system",
        "custodian",
        "authenticity_status",
        "hearsay_flag",
        "best_evidence_rule",
        "extracted_text",
        "key_facts",
        "entities_mentioned",
        "corroborates",
        "contradicts",
        "causally_linked_to",
        "temporal_sequence",
        "chain_of_custody",
        "alteration_history",
        "exhibit_number",
        "admissibility_assessment",
    ):
        assert key in d
    assert d["node_id"] == "EV-2026-000147"
    assert d["key_facts"][0]["confidence"] == 0.98


if __name__ == "__main__":
    test_sequential_ids_immutable_format()
    test_privilege_class_protected()
    test_relationships_and_key_facts()
    test_example_shape_matches_spec()
    print("OK: 4 evidence node tests passed")
