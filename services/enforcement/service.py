"""Enforcement support skeleton — RTB / Provincial Court pathways (info only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EnforcementTask:
    matter_id: str
    pathway: str  # rtb_enforcement | provincial_court | garnishment_research
    status: str = "not_started"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "matter_id": self.matter_id,
            "pathway": self.pathway,
            "status": self.status,
            "notes": self.notes,
        }


@dataclass
class EnforcementStub:
    tasks: list[EnforcementTask] = field(default_factory=list)

    def open_task(self, task: EnforcementTask) -> EnforcementTask:
        task.notes = (
            task.notes
            or "Verify current RTB / court enforcement procedures on official government sites."
        )
        self.tasks.append(task)
        return task
