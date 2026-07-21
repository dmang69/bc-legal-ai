"""
Matter-isolated evidence matrix store (JSONL under matters/{id}/evidence/).

Privilege and production gates live in backend.privilege — this module only
stores and queries EvidenceItem rows for a single matter_id.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from architecture.privilege_schemas import PrivilegeBasis, PrivilegeStatus
from architecture.schemas import AdmissibilityFlag, EvidenceItem, EvidenceType


class MatterScopeError(ValueError):
    """Raised when an operation would cross matter boundaries."""


class EvidenceMatrix:
    """In-memory matrix with optional durable JSONL persistence per matter."""

    def __init__(
        self,
        matter_id: str,
        *,
        root: Optional[Path] = None,
        auto_load: bool = True,
    ) -> None:
        if not matter_id or "/" in matter_id or "\\" in matter_id or ".." in matter_id:
            raise ValueError("matter_id must be a simple path-safe identifier")
        self.matter_id = matter_id
        self.root = (root or Path("matters")).resolve()
        self._items: dict[str, EvidenceItem] = {}
        if auto_load and self.matrix_path.is_file():
            self.load()

    @property
    def matter_dir(self) -> Path:
        return self.root / self.matter_id / "evidence"

    @property
    def matrix_path(self) -> Path:
        return self.matter_dir / "matrix.jsonl"

    @property
    def originals_dir(self) -> Path:
        return self.matter_dir / "originals"

    @property
    def derived_dir(self) -> Path:
        return self.matter_dir / "derived"

    def ensure_dirs(self) -> None:
        self.originals_dir.mkdir(parents=True, exist_ok=True)
        self.derived_dir.mkdir(parents=True, exist_ok=True)

    def _assert_matter(self, item: EvidenceItem) -> None:
        if item.matter_id and item.matter_id != self.matter_id:
            raise MatterScopeError(
                f"item matter_id={item.matter_id!r} != matrix matter_id={self.matter_id!r}"
            )
        item.matter_id = self.matter_id

    def add(self, item: EvidenceItem, *, persist: bool = True) -> EvidenceItem:
        self._assert_matter(item)
        self._items[item.evidence_id] = item
        if persist:
            self.save()
        return item

    def get(self, evidence_id: str) -> Optional[EvidenceItem]:
        return self._items.get(evidence_id)

    def all(self) -> list[EvidenceItem]:
        return list(self._items.values())

    def by_claim_tag(self, tag: str) -> list[EvidenceItem]:
        return [e for e in self._items.values() if tag in e.claim_tags]

    def by_type(self, evidence_type: EvidenceType) -> list[EvidenceItem]:
        return [e for e in self._items.values() if e.evidence_type == evidence_type]

    def locked_for_export(self) -> list[EvidenceItem]:
        return [e for e in self._items.values() if e.requires_privilege_gate()]

    def remove(self, evidence_id: str, *, persist: bool = True) -> bool:
        if evidence_id not in self._items:
            return False
        del self._items[evidence_id]
        if persist:
            self.save()
        return True

    def link_corroborates(self, a_id: str, b_id: str, *, persist: bool = True) -> None:
        a, b = self._pair(a_id, b_id)
        if b.evidence_id not in a.corroborates:
            a.corroborates.append(b.evidence_id)
        if a.evidence_id not in b.corroborates:
            b.corroborates.append(a.evidence_id)
        if persist:
            self.save()

    def link_contradicts(self, a_id: str, b_id: str, *, persist: bool = True) -> None:
        a, b = self._pair(a_id, b_id)
        if b.evidence_id not in a.contradicts:
            a.contradicts.append(b.evidence_id)
        if a.evidence_id not in b.contradicts:
            b.contradicts.append(a.evidence_id)
        if persist:
            self.save()

    def _pair(self, a_id: str, b_id: str) -> tuple[EvidenceItem, EvidenceItem]:
        a, b = self._items.get(a_id), self._items.get(b_id)
        if a is None or b is None:
            raise KeyError("both evidence IDs must exist in this matter matrix")
        return a, b

    def gap_report(self, claimed_tags: Iterable[str]) -> list[str]:
        covered: set[str] = set()
        for e in self._items.values():
            covered.update(e.claim_tags)
        return [t for t in claimed_tags if t not in covered]

    def save(self) -> Path:
        self.ensure_dirs()
        with self.matrix_path.open("w", encoding="utf-8") as f:
            for item in self._items.values():
                f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")
        return self.matrix_path

    def load(self) -> int:
        self._items.clear()
        if not self.matrix_path.is_file():
            return 0
        n = 0
        with self.matrix_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                item = item_from_dict(data)
                if item.matter_id and item.matter_id != self.matter_id:
                    raise MatterScopeError(
                        f"cross-matter row in {self.matrix_path}: {item.matter_id}"
                    )
                item.matter_id = self.matter_id
                self._items[item.evidence_id] = item
                n += 1
        return n

    def summary(self) -> dict:
        tags: dict[str, int] = {}
        locked = 0
        for e in self._items.values():
            for t in e.claim_tags:
                tags[t] = tags.get(t, 0) + 1
            if e.privilege_lock or e.requires_privilege_gate():
                locked += 1
        return {
            "matter_id": self.matter_id,
            "count": len(self._items),
            "claim_tag_counts": tags,
            "privilege_gated_count": locked,
            "contradiction_edges": sum(len(e.contradicts) for e in self._items.values()) // 2,
            "corroboration_edges": sum(len(e.corroborates) for e in self._items.values()) // 2,
        }


def item_from_dict(data: dict) -> EvidenceItem:
    """Deserialize matrix JSONL row (supports legacy id/content_sha256 keys)."""
    et = data.get("evidence_type", "other")
    af = data.get("admissibility_flag", "needs_verification")
    ps = data.get("privilege_state", data.get("privilege_status", "UNCLAIMED"))
    pb = data.get("privilege_basis", "none")
    eid = data.get("evidence_id") or data.get("id")
    fhash = data.get("file_hash") or data.get("content_sha256")

    custody = data.get("chain_of_custody")
    if custody is None:
        custody = []
    elif isinstance(custody, str):
        # legacy string form
        custody = [{"action": "legacy_note", "actor_id": "system", "detail": custody}]

    item = EvidenceItem(
        source_file=data["source_file"],
        matter_id=data.get("matter_id"),
        evidence_type=EvidenceType(et) if not isinstance(et, EvidenceType) else et,
        file_hash=fhash,
        privilege_state=(
            PrivilegeStatus(ps) if not isinstance(ps, PrivilegeStatus) else ps
        ),
        privilege_basis=(
            PrivilegeBasis(pb) if not isinstance(pb, PrivilegeBasis) else pb
        ),
        privilege_lock=bool(data.get("privilege_lock", False)),
        date_captured=data.get("date_captured"),
        date_received=data.get("date_received"),
        parties_referenced=list(data.get("parties_referenced") or []),
        location_referenced=data.get("location_referenced"),
        claim_tags=list(data.get("claim_tags") or []),
        contradicts=list(data.get("contradicts") or []),
        corroborates=list(data.get("corroborates") or []),
        hearing_relevance=float(data.get("hearing_relevance") or 0.0),
        admissibility_flag=(
            AdmissibilityFlag(af) if not isinstance(af, AdmissibilityFlag) else af
        ),
        ocr_confidence=float(data.get("ocr_confidence") or 0.0),
        human_notes=data.get("human_notes") or "",
        chain_of_custody=list(custody),
        page_count=data.get("page_count"),
        evidence_id=eid or str(__import__("uuid").uuid4()),
    )
    return item
