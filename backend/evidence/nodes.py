"""
EvidenceNode store — sequential IDs, graph edges, hearing readiness fields.

Persists beside matrix.jsonl as nodes.jsonl + seq_counter.json per matter.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from architecture.evidence_node import (
    EvidenceNode,
    KeyFact,
    PrivilegeClass,
    evidence_item_to_node,
)
from architecture.schemas import EvidenceItem
from backend.evidence.contradiction_engine import (
    ContradictionRunResult,
    detect_key_fact_contradictions,
)


class NodeIdError(ValueError):
    pass


class EvidenceNodeStore:
    """Matter-scoped EvidenceNode graph."""

    def __init__(
        self,
        matter_id: str,
        *,
        root: Optional[Path] = None,
        auto_load: bool = True,
    ) -> None:
        if not matter_id or "/" in matter_id or "\\" in matter_id or ".." in matter_id:
            raise ValueError("matter_id must be path-safe")
        self.matter_id = matter_id
        self.root = (root or Path("matters")).resolve()
        self._nodes: dict[str, EvidenceNode] = {}
        self._seq: int = 0
        if auto_load:
            self.load()

    @property
    def evidence_dir(self) -> Path:
        return self.root / self.matter_id / "evidence"

    @property
    def nodes_path(self) -> Path:
        return self.evidence_dir / "nodes.jsonl"

    @property
    def counter_path(self) -> Path:
        return self.evidence_dir / "seq_counter.json"

    def ensure_dirs(self) -> None:
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def _year(self) -> int:
        return datetime.now(timezone.utc).year

    def next_node_id(self) -> str:
        """Sequential immutable ID: EV-YYYY-NNNNNN."""
        self._seq += 1
        return f"EV-{self._year()}-{self._seq:06d}"

    def peek_next_id(self) -> str:
        return f"EV-{self._year()}-{self._seq + 1:06d}"

    def add(self, node: EvidenceNode, *, persist: bool = True) -> EvidenceNode:
        if node.matter_id and node.matter_id != self.matter_id:
            raise ValueError("cross-matter EvidenceNode rejected")
        node.matter_id = self.matter_id
        if not re.match(r"^EV-\d{4}-\d{6}$", node.node_id):
            raise NodeIdError(f"invalid node_id format: {node.node_id}")
        # extract sequence if higher
        seq = int(node.node_id.rsplit("-", 1)[-1])
        if seq > self._seq:
            self._seq = seq
        self._nodes[node.node_id] = node
        if persist:
            self.save()
        return node

    def allocate_from_item(
        self,
        item: EvidenceItem,
        *,
        extracted_text: str = "",
        custodian: str = "unknown",
        persist: bool = True,
    ) -> EvidenceNode:
        """Create sequential node from matrix row (idempotent on matrix_evidence_id)."""
        for n in self._nodes.values():
            if n.matrix_evidence_id == item.evidence_id:
                return n
        node_id = self.next_node_id()
        node = evidence_item_to_node(
            item,
            node_id=node_id,
            extracted_text=extracted_text,
            custodian=custodian,
        )
        return self.add(node, persist=persist)

    def get(self, node_id: str) -> Optional[EvidenceNode]:
        return self._nodes.get(node_id)

    def all(self) -> list[EvidenceNode]:
        return list(self._nodes.values())

    def by_hash(self, doc_hash: str) -> Optional[EvidenceNode]:
        bare = doc_hash[7:] if doc_hash.startswith("sha256:") else doc_hash
        for n in self._nodes.values():
            if n.bare_hash() == bare:
                return n
        return None

    def link_corroborates(self, a: str, b: str, *, persist: bool = True) -> None:
        na, nb = self._pair(a, b)
        if b not in na.corroborates:
            na.corroborates.append(b)
        if a not in nb.corroborates:
            nb.corroborates.append(a)
        if persist:
            self.save()

    def link_contradicts(self, a: str, b: str, *, persist: bool = True) -> None:
        na, nb = self._pair(a, b)
        if b not in na.contradicts:
            na.contradicts.append(b)
        if a not in nb.contradicts:
            nb.contradicts.append(a)
        if persist:
            self.save()

    def link_causal(self, a: str, b: str, *, persist: bool = True) -> None:
        na, _ = self._pair(a, b)
        if b not in na.causally_linked_to:
            na.causally_linked_to.append(b)
        if persist:
            self.save()

    def set_temporal(self, earlier: str, later: str, *, persist: bool = True) -> None:
        e, l = self._pair(earlier, later)
        if later not in e.temporal_sequence.after:
            e.temporal_sequence.after.append(later)
        if earlier not in l.temporal_sequence.before:
            l.temporal_sequence.before.append(earlier)
        if persist:
            self.save()

    def assign_exhibit(self, node_id: str, exhibit_number: str, *, persist: bool = True) -> None:
        n = self._nodes.get(node_id)
        if not n:
            raise KeyError(node_id)
        n.exhibit_number = exhibit_number
        if persist:
            self.save()

    def add_key_fact(
        self,
        node_id: str,
        fact: str,
        *,
        confidence: float = 0.0,
        source_span: Optional[str] = None,
        persist: bool = True,
    ) -> None:
        n = self._nodes.get(node_id)
        if not n:
            raise KeyError(node_id)
        n.key_facts.append(
            KeyFact(fact=fact, confidence=confidence, source_span=source_span)
        )
        if persist:
            self.save()

    def protected_nodes(self) -> list[EvidenceNode]:
        return [n for n in self._nodes.values() if n.requires_privilege_gate()]

    def run_contradiction_scan(self, *, persist: bool = True) -> ContradictionRunResult:
        """Pairwise key-fact contradiction pass; mutates nodes in place."""
        result = detect_key_fact_contradictions(self.all(), apply_edges=True)
        if persist:
            self.save()
        return result

    def score_strength(self, *, persist: bool = True) -> dict:
        """Assign strength_score / strength_tier to every node."""
        from backend.evidence.strength import (
            apply_strength_to_node,
            format_strength_report,
            tier_buckets,
        )

        assessments = []
        for n in self.all():
            a = apply_strength_to_node(n)
            assessments.append({"node_id": n.node_id, **a.to_dict()})
        if persist:
            self.save()
        return {
            "assessments": assessments,
            "buckets": tier_buckets(self.all()),
            "report": format_strength_report(self.all()),
        }

    def rebuild_temporal_from_dates(self, *, persist: bool = True) -> int:
        """Order nodes by date_created/date_received and set before/after chains."""
        dated: list[tuple[str, EvidenceNode]] = []
        for n in self._nodes.values():
            d = n.date_created or n.date_received
            if d:
                dated.append((d[:10], n))
        dated.sort(key=lambda x: x[0])
        links = 0
        for i in range(len(dated) - 1):
            earlier_id = dated[i][1].node_id
            later_id = dated[i + 1][1].node_id
            self.set_temporal(earlier_id, later_id, persist=False)
            links += 1
        if persist and links:
            self.save()
        return links

    def _pair(self, a: str, b: str) -> tuple[EvidenceNode, EvidenceNode]:
        na, nb = self._nodes.get(a), self._nodes.get(b)
        if na is None or nb is None:
            raise KeyError("both node_ids must exist")
        return na, nb

    def save(self) -> Path:
        self.ensure_dirs()
        with self.nodes_path.open("w", encoding="utf-8") as f:
            for n in sorted(self._nodes.values(), key=lambda x: x.node_id):
                f.write(json.dumps(n.to_dict(), ensure_ascii=False) + "\n")
        self.counter_path.write_text(
            json.dumps({"seq": self._seq, "year": self._year()}, indent=2) + "\n",
            encoding="utf-8",
        )
        return self.nodes_path

    def load(self) -> int:
        self._nodes.clear()
        self._seq = 0
        if self.counter_path.is_file():
            try:
                c = json.loads(self.counter_path.read_text(encoding="utf-8"))
                self._seq = int(c.get("seq") or 0)
            except (json.JSONDecodeError, ValueError):
                self._seq = 0
        if not self.nodes_path.is_file():
            return 0
        n = 0
        with self.nodes_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                node = EvidenceNode.from_dict(json.loads(line))
                self._nodes[node.node_id] = node
                seq = int(node.node_id.rsplit("-", 1)[-1])
                if seq > self._seq:
                    self._seq = seq
                n += 1
        return n

    def summary(self) -> dict:
        by_type: dict[str, int] = {}
        by_priv: dict[str, int] = {}
        for node in self._nodes.values():
            by_type[node.source_type.value] = by_type.get(node.source_type.value, 0) + 1
            by_priv[node.privilege_class.value] = (
                by_priv.get(node.privilege_class.value, 0) + 1
            )
        return {
            "matter_id": self.matter_id,
            "count": len(self._nodes),
            "next_node_id": self.peek_next_id(),
            "by_source_type": by_type,
            "by_privilege_class": by_priv,
            "protected_count": len(self.protected_nodes()),
        }


def sync_items_to_nodes(
    items: Iterable[EvidenceItem],
    store: EvidenceNodeStore,
    *,
    custodian: str = "unknown",
) -> list[EvidenceNode]:
    """Ensure every matrix item has a sequential EvidenceNode."""
    out: list[EvidenceNode] = []
    for item in items:
        out.append(store.allocate_from_item(item, custodian=custodian, persist=False))
    store.save()
    store.rebuild_temporal_from_dates(persist=True)
    return out
