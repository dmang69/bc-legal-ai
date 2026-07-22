"""
Primary source registry — statutes (BC Laws), cases, rules, point-in-time locks.

Statute text: BC Laws only. Cases: CanLII / courts (decisions only).
Not legal advice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SourceRecord:
    source_id: str
    title: str
    kind: str  # statute | regulation | case | rule | form | policy | tribunal_decision
    official_url: str
    citation: str = ""
    jurisdiction: str = "BC"
    current_to: Optional[str] = None
    accessed: Optional[str] = None
    version_lock: Optional[str] = None  # point-in-time pin for analysis as of event date
    event_date_law: Optional[str] = None  # ISO date law applied as of
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "kind": self.kind,
            "official_url": self.official_url,
            "citation": self.citation,
            "jurisdiction": self.jurisdiction,
            "current_to": self.current_to,
            "accessed": self.accessed,
            "version_lock": self.version_lock,
            "event_date_law": self.event_date_law,
            "notes": self.notes,
        }


_SEED: list[SourceRecord] = [
    SourceRecord(
        source_id="RTA-SBC-2002-c78",
        title="Residential Tenancy Act, SBC 2002, c 78",
        kind="statute",
        official_url="https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/02078_01",
        citation="SBC 2002, c 78",
        current_to="July 14, 2026",
        accessed="2026-07-21",
        notes="Re-verify currency line before filing. Point-in-time if event pre-dates amendments.",
    ),
    SourceRecord(
        source_id="JRPA-RSBC-1996-c241",
        title="Judicial Review Procedure Act, RSBC 1996, c 241",
        kind="statute",
        official_url="https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/96241_01",
        citation="RSBC 1996, c 241",
    ),
    SourceRecord(
        source_id="MHPTA-SBC-2002-c77",
        title="Manufactured Home Park Tenancy Act, SBC 2002, c 77",
        kind="statute",
        official_url="https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/02077_01",
        citation="SBC 2002, c 77",
    ),
    SourceRecord(
        source_id="RTB-RULES",
        title="Residential Tenancy Branch Rules of Procedure",
        kind="rule",
        official_url="https://www2.gov.bc.ca/gov/content/housing-tenancy/residential-tenancies",
        notes="Confirm current Rules on government site before filing.",
    ),
    SourceRecord(
        source_id="CANLII-BC",
        title="CanLII British Columbia (decisions index)",
        kind="case_index",
        official_url="https://www.canlii.org/en/bc/",
        notes="Cases only — never statute text for court packages.",
    ),
    SourceRecord(
        source_id="VAVILOV-2019-SCC-65",
        title="Canada (Minister of Citizenship and Immigration) v. Vavilov, 2019 SCC 65",
        kind="case",
        official_url="https://www.canlii.org/en/ca/scc/doc/2019/2019scc65/2019scc65.html",
        citation="2019 SCC 65",
        jurisdiction="SCC",
        notes="Standard of review framework — verify pinpoints on CanLII.",
    ),
]


@dataclass
class PointInTimeLock:
    source_id: str
    as_of_date: str
    version_lock: str
    reason: str = "analysis uses law as of event date"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "as_of_date": self.as_of_date,
            "version_lock": self.version_lock,
            "reason": self.reason,
        }


@dataclass
class PrimarySourceRegistry:
    records: list[SourceRecord] = field(default_factory=lambda: list(_SEED))
    locks: list[PointInTimeLock] = field(default_factory=list)

    def get(self, source_id: str) -> Optional[SourceRecord]:
        for r in self.records:
            if r.source_id == source_id:
                return r
        return None

    def by_kind(self, kind: str) -> list[SourceRecord]:
        return [r for r in self.records if r.kind == kind]

    def lock_version(
        self,
        source_id: str,
        *,
        version_lock: str,
        current_to: str,
        as_of_date: Optional[str] = None,
    ) -> Optional[SourceRecord]:
        rec = self.get(source_id)
        if not rec:
            return None
        rec.version_lock = version_lock
        rec.current_to = current_to
        if as_of_date:
            rec.event_date_law = as_of_date
            self.locks.append(
                PointInTimeLock(
                    source_id=source_id,
                    as_of_date=as_of_date,
                    version_lock=version_lock,
                )
            )
        return rec

    def law_as_of(self, source_id: str, event_date: str) -> Optional[PointInTimeLock]:
        """Return lock for analysis as of event date if recorded."""
        for lock in reversed(self.locks):
            if lock.source_id == source_id and lock.as_of_date <= event_date:
                return lock
        rec = self.get(source_id)
        if rec and rec.version_lock and rec.event_date_law:
            return PointInTimeLock(
                source_id=source_id,
                as_of_date=rec.event_date_law,
                version_lock=rec.version_lock,
            )
        return None
