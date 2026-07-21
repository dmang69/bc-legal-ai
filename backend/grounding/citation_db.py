"""
Verified citation registry (local workbench DB).

Only VERIFIED entries satisfy GroundingGate legal_basis checks.
PARTIALLY_VERIFIED does not pass fail-closed grounding.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from uuid import uuid4

from architecture.grounding import Citation
from architecture.schemas import AuthorityStatus


class CitationDB:
    """Matter- or workspace-scoped citation store."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path
        self._by_id: dict[str, Citation] = {}
        self._by_key: dict[str, str] = {}  # normalized short_cite/neutral → id
        if path and path.is_file():
            self.load()

    @staticmethod
    def _key(text: str) -> str:
        return " ".join((text or "").lower().split())

    def upsert(self, citation: Citation) -> Citation:
        if not citation.citation_id:
            citation.citation_id = f"CIT-{uuid4().hex[:10]}"
        self._by_id[citation.citation_id] = citation
        if citation.short_cite:
            self._by_key[self._key(citation.short_cite)] = citation.citation_id
        if citation.neutral_citation:
            self._by_key[self._key(citation.neutral_citation)] = citation.citation_id
        if citation.section and citation.short_cite:
            self._by_key[
                self._key(f"{citation.short_cite} s.{citation.section}")
            ] = citation.citation_id
        if self.path:
            self.save()
        return citation

    def get(self, citation_id: str) -> Optional[Citation]:
        return self._by_id.get(citation_id)

    def resolve(self, citation: Citation) -> Optional[Citation]:
        if citation.citation_id and citation.citation_id in self._by_id:
            return self._by_id[citation.citation_id]
        for candidate in (
            citation.neutral_citation,
            citation.short_cite,
            f"{citation.short_cite} s.{citation.section}"
            if citation.section
            else None,
        ):
            if not candidate:
                continue
            cid = self._by_key.get(self._key(candidate))
            if cid:
                return self._by_id[cid]
        return None

    def is_verified(self, citation: Citation) -> bool:
        found = self.resolve(citation)
        if not found:
            return False
        return found.status == AuthorityStatus.VERIFIED

    def all_verified(self) -> list[Citation]:
        return [c for c in self._by_id.values() if c.status == AuthorityStatus.VERIFIED]

    def save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        rows = [c.to_dict() for c in self._by_id.values()]
        self.path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")

    def load(self) -> int:
        if not self.path or not self.path.is_file():
            return 0
        data = json.loads(self.path.read_text(encoding="utf-8"))
        n = 0
        for row in data:
            self.upsert(Citation.from_dict(row))
            n += 1
        return n


def seed_bc_workbench_citations(db: CitationDB) -> CitationDB:
    """
    Seed non-exhaustive verified *registry entries* for workbench demos.

    Status VERIFIED here means "registered as checked in this workbench DB"
    with a BC Laws URL for statutes — re-verify currency before filing.
    """
    seeds = [
        Citation(
            short_cite="RTA s. 28",
            section="28",
            official_title="Residential Tenancy Act — quiet enjoyment",
            source_url="https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/02078_01",
            status=AuthorityStatus.VERIFIED,
            jurisdiction="BC",
        ),
        Citation(
            short_cite="RTA s. 32",
            section="32",
            official_title="Residential Tenancy Act — repair and maintain",
            source_url="https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/02078_01",
            status=AuthorityStatus.VERIFIED,
            jurisdiction="BC",
        ),
        Citation(
            short_cite="RTA s. 5",
            section="5",
            official_title="Residential Tenancy Act — cannot contract out",
            source_url="https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/02078_01",
            status=AuthorityStatus.VERIFIED,
            jurisdiction="BC",
        ),
        Citation(
            short_cite="RTA s. 29",
            section="29",
            official_title="Residential Tenancy Act — entry",
            source_url="https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/02078_01",
            status=AuthorityStatus.VERIFIED,
            jurisdiction="BC",
        ),
        Citation(
            short_cite="2019 SCC 65",
            neutral_citation="2019 SCC 65",
            official_title="Canada (Minister of Citizenship and Immigration) v. Vavilov",
            status=AuthorityStatus.VERIFIED,
            jurisdiction="Canada",
        ),
        # Intentionally not verified — for refusal tests
        Citation(
            short_cite="Fake v Imaginary",
            neutral_citation="2099 BCSC 1",
            status=AuthorityStatus.UNVERIFIED,
            jurisdiction="BC",
        ),
    ]
    for c in seeds:
        db.upsert(c)
    return db
