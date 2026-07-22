"""
Compliance Monitoring Engine — deadlines, evidence, non-compliance triggers.

Not legal advice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from services.post_resolution.outcome_tracker.engine import ComplianceClock, OutcomeTracker


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ComplianceStatus(str, Enum):
    PENDING = "PENDING"
    FULL = "FULL"
    PARTIAL = "PARTIAL"
    NON_COMPLIANT = "NON_COMPLIANT"
    DISPUTED = "DISPUTED"


class NonComplianceKind(str, Enum):
    MISSED_DEADLINE = "MISSED_DEADLINE"
    PARTIAL_COMPLIANCE = "PARTIAL_COMPLIANCE"
    CONTRADICTORY_EVIDENCE = "CONTRADICTORY_EVIDENCE"
    NO_EVIDENCE = "NO_EVIDENCE"


@dataclass
class ComplianceEvidence:
    evidence_id: str
    matter_id: str
    obligation_id: str
    kind: str  # photo | receipt | inspection_report | other
    filename: str
    note: str = ""
    node_id: Optional[str] = None
    uploaded_at: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "matter_id": self.matter_id,
            "obligation_id": self.obligation_id,
            "kind": self.kind,
            "filename": self.filename,
            "note": self.note,
            "node_id": self.node_id,
            "uploaded_at": self.uploaded_at,
        }


@dataclass
class Reminder:
    reminder_id: str
    matter_id: str
    clock_id: str
    party: str
    due_date: Optional[str]
    message: str
    sent_at: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reminder_id": self.reminder_id,
            "matter_id": self.matter_id,
            "clock_id": self.clock_id,
            "party": self.party,
            "due_date": self.due_date,
            "message": self.message,
            "sent_at": self.sent_at,
        }


@dataclass
class NonComplianceEvent:
    event_id: str
    matter_id: str
    obligation_id: str
    kind: NonComplianceKind
    message: str
    ts: str = field(default_factory=_utcnow)
    escalated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "matter_id": self.matter_id,
            "obligation_id": self.obligation_id,
            "kind": self.kind.value,
            "message": self.message,
            "ts": self.ts,
            "escalated": self.escalated,
        }


@dataclass
class ComplianceLedgerEntry:
    matter_id: str
    obligation_id: str
    status: ComplianceStatus
    notes: str = ""
    updated_at: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "matter_id": self.matter_id,
            "obligation_id": self.obligation_id,
            "status": self.status.value,
            "notes": self.notes,
            "updated_at": self.updated_at,
        }


@dataclass
class ComplianceLedger:
    entries: dict[str, ComplianceLedgerEntry] = field(default_factory=dict)  # key obligation_id

    def upsert(self, entry: ComplianceLedgerEntry) -> ComplianceLedgerEntry:
        self.entries[entry.obligation_id] = entry
        return entry

    def for_matter(self, matter_id: str) -> list[ComplianceLedgerEntry]:
        return [e for e in self.entries.values() if e.matter_id == matter_id]


@dataclass
class ComplianceMonitor:
    ledger: ComplianceLedger = field(default_factory=ComplianceLedger)
    evidence: list[ComplianceEvidence] = field(default_factory=list)
    reminders: list[Reminder] = field(default_factory=list)
    events: list[NonComplianceEvent] = field(default_factory=list)
    outcome_tracker: Optional[OutcomeTracker] = None

    def seed_from_tracker(self, tracker: OutcomeTracker, matter_id: str) -> None:
        self.outcome_tracker = tracker
        rec = tracker.get(matter_id)
        if not rec:
            return
        for obl in rec.obligations:
            if obl.kind.value == "DISMISSAL":
                continue
            self.ledger.upsert(
                ComplianceLedgerEntry(
                    matter_id=matter_id,
                    obligation_id=obl.obligation_id,
                    status=ComplianceStatus.PENDING,
                )
            )

    def add_evidence(
        self,
        *,
        matter_id: str,
        obligation_id: str,
        kind: str,
        filename: str,
        note: str = "",
        node_id: Optional[str] = None,
    ) -> ComplianceEvidence:
        ev = ComplianceEvidence(
            evidence_id=f"CEV-{uuid4().hex[:10]}",
            matter_id=matter_id,
            obligation_id=obligation_id,
            kind=kind,
            filename=filename,
            note=note,
            node_id=node_id,
        )
        self.evidence.append(ev)
        return ev

    def generate_reminders(
        self,
        matter_id: str,
        clocks: list[ComplianceClock],
        *,
        today: Optional[date] = None,
        within_days: int = 7,
    ) -> list[Reminder]:
        t = today or date.today()
        out: list[Reminder] = []
        for c in clocks:
            if c.matter_id != matter_id or c.status != "OPEN" or not c.due_date:
                continue
            try:
                due = date.fromisoformat(c.due_date[:10])
            except ValueError:
                continue
            days_left = (due - t).days
            if 0 <= days_left <= within_days:
                msg = (
                    f"Reminder: {c.label} — due {c.due_date} ({days_left} day(s) remaining)."
                )
                r = Reminder(
                    reminder_id=f"REM-{uuid4().hex[:10]}",
                    matter_id=matter_id,
                    clock_id=c.clock_id,
                    party=c.party,
                    due_date=c.due_date,
                    message=msg,
                )
                self.reminders.append(r)
                out.append(r)
        return out

    def detect_non_compliance(
        self,
        matter_id: str,
        clocks: list[ComplianceClock],
        *,
        today: Optional[date] = None,
    ) -> list[NonComplianceEvent]:
        t = today or date.today()
        found: list[NonComplianceEvent] = []
        for c in clocks:
            if c.matter_id != matter_id or c.status in ("DONE", "WAIVED"):
                continue
            entry = self.ledger.entries.get(c.obligation_id)
            evs = [e for e in self.evidence if e.obligation_id == c.obligation_id]

            if c.due_date:
                try:
                    due = date.fromisoformat(c.due_date[:10])
                except ValueError:
                    due = None
                if due and t > due:
                    if not entry or entry.status != ComplianceStatus.FULL:
                        kind = (
                            NonComplianceKind.PARTIAL_COMPLIANCE
                            if entry and entry.status == ComplianceStatus.PARTIAL
                            else NonComplianceKind.MISSED_DEADLINE
                        )
                        if not evs and kind == NonComplianceKind.MISSED_DEADLINE:
                            kind = NonComplianceKind.MISSED_DEADLINE
                        evt = NonComplianceEvent(
                            event_id=f"NCE-{uuid4().hex[:10]}",
                            matter_id=matter_id,
                            obligation_id=c.obligation_id,
                            kind=kind,
                            message=f"Deadline passed ({c.due_date}): {c.label}",
                        )
                        self.events.append(evt)
                        found.append(evt)
                        if entry:
                            entry.status = ComplianceStatus.NON_COMPLIANT
                            entry.updated_at = _utcnow()

            # Contradictory evidence heuristic
            notes = " ".join(e.note.lower() for e in evs)
            if "not repaired" in notes and "completed" in notes:
                evt = NonComplianceEvent(
                    event_id=f"NCE-{uuid4().hex[:10]}",
                    matter_id=matter_id,
                    obligation_id=c.obligation_id,
                    kind=NonComplianceKind.CONTRADICTORY_EVIDENCE,
                    message="Contradictory compliance evidence notes detected.",
                )
                self.events.append(evt)
                found.append(evt)

            if entry and entry.status == ComplianceStatus.PARTIAL:
                evt = NonComplianceEvent(
                    event_id=f"NCE-{uuid4().hex[:10]}",
                    matter_id=matter_id,
                    obligation_id=c.obligation_id,
                    kind=NonComplianceKind.PARTIAL_COMPLIANCE,
                    message="Ledger marked PARTIAL compliance.",
                )
                # avoid dupes on every poll
                if not any(
                    e.obligation_id == c.obligation_id
                    and e.kind == NonComplianceKind.PARTIAL_COMPLIANCE
                    for e in self.events
                ):
                    self.events.append(evt)
                    found.append(evt)

        return found

    def mark_status(
        self,
        matter_id: str,
        obligation_id: str,
        status: ComplianceStatus,
        notes: str = "",
    ) -> ComplianceLedgerEntry:
        return self.ledger.upsert(
            ComplianceLedgerEntry(
                matter_id=matter_id,
                obligation_id=obligation_id,
                status=status,
                notes=notes,
            )
        )
