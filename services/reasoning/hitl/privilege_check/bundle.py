"""Waiver-risk: privileged document inside an evidence production bundle."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from architecture.evidence_node import EvidenceNode, PrivilegeClass
from services.reasoning.hitl.privilege_check.scan import scan_pre_output


@dataclass
class BundleScanResult:
    safe_to_produce: bool
    privileged_node_ids: list[str] = field(default_factory=list)
    restricted_node_ids: list[str] = field(default_factory=list)
    text_hits: list[str] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "safe_to_produce": self.safe_to_produce,
            "privileged_node_ids": list(self.privileged_node_ids),
            "restricted_node_ids": list(self.restricted_node_ids),
            "text_hits": list(self.text_hits),
            "message": self.message,
        }


def scan_evidence_bundle(
    nodes: Iterable[EvidenceNode],
    *,
    production_gate_cleared_ids: Optional[set[str]] = None,
) -> BundleScanResult:
    cleared = production_gate_cleared_ids or set()
    priv: list[str] = []
    rest: list[str] = []
    text_hits: list[str] = []
    for n in nodes:
        if n.privilege_class == PrivilegeClass.PROTECTED and n.node_id not in cleared:
            priv.append(n.node_id)
        if n.privilege_class == PrivilegeClass.RESTRICTED and n.node_id not in cleared:
            rest.append(n.node_id)
        scan = scan_pre_output(n.extracted_text or "")
        if not scan.clean and n.node_id not in cleared:
            text_hits.append(n.node_id)
    blocked = bool(priv or rest or text_hits)
    return BundleScanResult(
        safe_to_produce=not blocked,
        privileged_node_ids=priv,
        restricted_node_ids=rest,
        text_hits=text_hits,
        message=(
            "Bundle contains privileged/restricted material — production blocked."
            if blocked
            else "No uncleared privileged nodes detected in bundle."
        ),
    )
