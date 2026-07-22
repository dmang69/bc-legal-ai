"""
Retention schedule engine — evidence, privileged, client comms, drafts.

Defaults are illustrative. Firm + LSBC rules override. Not legal advice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from services.compliance.lsbc_rules.rules import LsbcRetentionRules, default_lsbc_rules


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class RetentionCategory(str, Enum):
    EVIDENCE = "EVIDENCE"
    PRIVILEGED = "PRIVILEGED"
    CLIENT_COMMS = "CLIENT_COMMS"
    DRAFTS = "DRAFTS"
    AUDIT = "AUDIT"


@dataclass
class RetentionItem:
    item_id: str
    matter_id: str
    category: RetentionCategory
    object_ref: str
    retain_until: Optional[str]
    on_hold: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "matter_id": self.matter_id,
            "category": self.category.value,
            "object_ref": self.object_ref,
            "retain_until": self.retain_until,
            "on_hold": self.on_hold,
        }


@dataclass
class MatterClosurePlan:
    matter_id: str
    closed_on: str
    final_summary: str
    retention_plan: list[dict[str, Any]]
    privilege_lock: bool = True
    access_frozen: bool = True
    plan_id: str = field(default_factory=lambda: f"MCP-{uuid4().hex[:10]}")
    created_at: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "matter_id": self.matter_id,
            "closed_on": self.closed_on,
            "final_summary": self.final_summary,
            "retention_plan": list(self.retention_plan),
            "privilege_lock": self.privilege_lock,
            "access_frozen": self.access_frozen,
            "created_at": self.created_at,
        }


@dataclass
class RetentionScheduleEngine:
    rules: LsbcRetentionRules = field(default_factory=default_lsbc_rules)
    items: list[RetentionItem] = field(default_factory=list)
    holds: set[str] = field(default_factory=set)
    closures: dict[str, MatterClosurePlan] = field(default_factory=dict)
    access_frozen: set[str] = field(default_factory=set)

    def years_for(self, category: RetentionCategory) -> int:
        m = {
            RetentionCategory.EVIDENCE: self.rules.min_evidence_years,
            RetentionCategory.PRIVILEGED: self.rules.min_privileged_years,
            RetentionCategory.CLIENT_COMMS: self.rules.min_client_comms_years,
            RetentionCategory.DRAFTS: self.rules.min_drafts_years,
            RetentionCategory.AUDIT: self.rules.min_audit_years,
        }
        return m[category]

    def schedule_item(
        self,
        *,
        matter_id: str,
        category: RetentionCategory,
        object_ref: str,
        closed_on: Optional[str] = None,
    ) -> RetentionItem:
        retain_until = None
        if closed_on:
            try:
                d = date.fromisoformat(closed_on[:10])
                y = self.years_for(category)
                retain_until = date(d.year + y, d.month, d.day).isoformat()
            except ValueError:
                retain_until = None
        item = RetentionItem(
            item_id=f"RET-{uuid4().hex[:10]}",
            matter_id=matter_id,
            category=category,
            object_ref=object_ref,
            retain_until=retain_until,
            on_hold=matter_id in self.holds,
        )
        self.items.append(item)
        return item

    def place_hold(self, matter_id: str) -> None:
        self.holds.add(matter_id)
        for i in self.items:
            if i.matter_id == matter_id:
                i.on_hold = True

    def release_hold(self, matter_id: str) -> None:
        self.holds.discard(matter_id)
        # conflict exception may re-hold — caller decides

    def close_matter(
        self,
        *,
        matter_id: str,
        closed_on: str,
        final_summary: str,
        object_refs: Optional[dict[str, list[str]]] = None,
    ) -> MatterClosurePlan:
        """
        Matter closure protocol: final summary, retention plan, privilege lock, access freeze.
        object_refs: category name -> list of refs
        """
        plan_rows: list[dict[str, Any]] = []
        refs = object_refs or {}
        for cat in RetentionCategory:
            for ref in refs.get(cat.value, refs.get(cat.name, [])):
                item = self.schedule_item(
                    matter_id=matter_id,
                    category=cat,
                    object_ref=ref,
                    closed_on=closed_on,
                )
                plan_rows.append(item.to_dict())
        if not plan_rows:
            # default plan rows by category
            for cat in RetentionCategory:
                plan_rows.append(
                    {
                        "category": cat.value,
                        "years": self.years_for(cat),
                        "note": self.rules.notes,
                    }
                )
        plan = MatterClosurePlan(
            matter_id=matter_id,
            closed_on=closed_on,
            final_summary=final_summary,
            retention_plan=plan_rows,
            privilege_lock=True,
            access_frozen=True,
        )
        self.closures[matter_id] = plan
        self.access_frozen.add(matter_id)
        return plan

    def is_access_frozen(self, matter_id: str) -> bool:
        return matter_id in self.access_frozen
