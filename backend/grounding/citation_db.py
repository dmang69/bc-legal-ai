"""
Verified citation registry (local workbench DB).

Only VERIFIED, non-superseded entries satisfy GroundingGate legal_basis checks.
Statute exact_text must come from BC Laws at verification — never invent wording.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from uuid import uuid4

from architecture.grounding import Citation, CitationType, JurisdictionScope
from architecture.schemas import AuthorityStatus


_BC_LAWS_RTA = (
    "https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/02078_01"
)
_VERIFIED_ON = "2026-07-21"  # registry check date; re-verify currency line before filing


class CitationDB:
    """Matter- or workspace-scoped citation store."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path
        self._by_id: dict[str, Citation] = {}
        self._by_key: dict[str, str] = {}  # normalized lookup → citation_id
        if path and path.is_file():
            self.load()

    @staticmethod
    def _key(text: str) -> str:
        return " ".join((text or "").lower().split())

    def upsert(self, citation: Citation, *, persist: bool = True) -> Citation:
        citation.ensure_ids_and_hash()
        assert citation.citation_id
        self._by_id[citation.citation_id] = citation
        keys = [
            citation.citation_id,
            citation.short_cite,
            citation.display_cite(),
            citation.neutral_citation,
            citation.citation,
            citation.case_name,
        ]
        if citation.act and citation.section:
            keys.append(f"{citation.act} s. {citation.section}")
            keys.append(f"rta s. {citation.section}")
            keys.append(f"rta s.{citation.section}")
            if citation.subsection:
                keys.append(f"rta s. {citation.section}({citation.subsection})")
        for k in keys:
            if k:
                self._by_key[self._key(k)] = citation.citation_id
        for tag in citation.applies_to:
            # secondary index key
            self._by_key[self._key(f"tag:{tag}:{citation.citation_id}")] = citation.citation_id
        if persist and self.path:
            self.save()
        return citation

    def get(self, citation_id: str) -> Optional[Citation]:
        return self._by_id.get(citation_id)

    def resolve(self, citation: Citation) -> Optional[Citation]:
        if citation.citation_id and citation.citation_id in self._by_id:
            return self._by_id[citation.citation_id]
        candidates = [
            citation.citation_id,
            citation.neutral_citation,
            citation.citation,
            citation.short_cite,
            citation.case_name,
            citation.display_cite(),
        ]
        if citation.section:
            candidates.append(f"RTA s. {citation.section}")
            candidates.append(f"rta s. {citation.section}")
            if citation.act:
                candidates.append(f"{citation.act} s. {citation.section}")
        for candidate in candidates:
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
        if found.superseded_by:
            return False
        return found.status == AuthorityStatus.VERIFIED

    def by_applies_to(self, tag: str) -> list[Citation]:
        tag_l = tag.lower()
        return [
            c
            for c in self._by_id.values()
            if any(t.lower() == tag_l for t in c.applies_to)
            and c.status == AuthorityStatus.VERIFIED
            and not c.superseded_by
        ]

    def all_verified(self) -> list[Citation]:
        return [
            c
            for c in self._by_id.values()
            if c.status == AuthorityStatus.VERIFIED and not c.superseded_by
        ]

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
            self.upsert(Citation.from_dict(row), persist=False)
            n += 1
        return n


def seed_bc_workbench_citations(db: CitationDB) -> CitationDB:
    """
    Seed registry metadata for workbench demos.

    exact_text is left null for statutes — pull official wording from BC Laws
    before court use. VERIFIED = registry entry checked against pin map / known case.
    """
    rta_url = _BC_LAWS_RTA
    seeds = [
        Citation(
            citation_id="CIT-RTA-S5",
            type=CitationType.STATUTE,
            jurisdiction="BC",
            act="Residential Tenancy Act",
            section="5",
            short_cite="RTA s. 5",
            official_title="Residential Tenancy Act — cannot contract out",
            source_url=rta_url,
            last_verified=_VERIFIED_ON,
            applies_to=["contracting_out"],
            jurisdiction_scope=JurisdictionScope.BC,
            status=AuthorityStatus.VERIFIED,
        ),
        Citation(
            citation_id="CIT-RTA-S28",
            type=CitationType.STATUTE,
            jurisdiction="BC",
            act="Residential Tenancy Act",
            section="28",
            short_cite="RTA s. 28",
            official_title="Residential Tenancy Act — quiet enjoyment",
            source_url=rta_url,
            last_verified=_VERIFIED_ON,
            applies_to=["quiet_enjoyment"],
            jurisdiction_scope=JurisdictionScope.BC,
            status=AuthorityStatus.VERIFIED,
        ),
        Citation(
            citation_id="CIT-RTA-S29",
            type=CitationType.STATUTE,
            jurisdiction="BC",
            act="Residential Tenancy Act",
            section="29",
            short_cite="RTA s. 29",
            official_title="Residential Tenancy Act — entry",
            source_url=rta_url,
            last_verified=_VERIFIED_ON,
            applies_to=["entry"],
            jurisdiction_scope=JurisdictionScope.BC,
            status=AuthorityStatus.VERIFIED,
        ),
        Citation(
            citation_id="CIT-RTA-S32",
            type=CitationType.STATUTE,
            jurisdiction="BC",
            act="Residential Tenancy Act",
            section="32",
            short_cite="RTA s. 32",
            official_title="Residential Tenancy Act — repair and maintain",
            source_url=rta_url,
            last_verified=_VERIFIED_ON,
            applies_to=["non_repair", "mold_hazard", "habitability"],
            jurisdiction_scope=JurisdictionScope.BC,
            status=AuthorityStatus.VERIFIED,
        ),
        Citation(
            citation_id="CIT-RTA-S38",
            type=CitationType.STATUTE,
            jurisdiction="BC",
            act="Residential Tenancy Act",
            section="38",
            short_cite="RTA s. 38",
            official_title="Residential Tenancy Act — deposit return",
            source_url=rta_url,
            last_verified=_VERIFIED_ON,
            applies_to=["deposit"],
            jurisdiction_scope=JurisdictionScope.BC,
            status=AuthorityStatus.VERIFIED,
        ),
        # Structure for retaliatory eviction pin — exact_text NOT invented;
        # re-verify section number and wording on BC Laws before filing.
        Citation(
            citation_id="CIT-RTA-S56",
            type=CitationType.STATUTE,
            jurisdiction="BC",
            act="Residential Tenancy Act",
            section="56",
            subsection="1",
            short_cite="RTA s. 56",
            official_title="Residential Tenancy Act — (verify subject on BC Laws: often cited for retaliation issues)",
            exact_text=None,
            source_url=rta_url,
            last_verified=_VERIFIED_ON,
            applies_to=["retaliatory_eviction"],
            jurisdiction_scope=JurisdictionScope.BC,
            status=AuthorityStatus.PARTIALLY_VERIFIED,  # pin structure only; not fail-closed ready
        ),
        Citation(
            citation_id="CIT-DESC-MIERZ",
            type=CitationType.CASE_LAW,
            jurisdiction="Canada",
            case_name="Descoteaux v. Mierzwinski",
            citation="[1982] 2 SCR 890",
            neutral_citation="[1982] 2 SCR 890",
            short_cite="Descoteaux v. Mierzwinski, [1982] 2 SCR 890",
            principle_established="Solicitor-client privilege belongs to the client",
            parenthetical="privilege is client's right alone to waive",
            source_url="https://www.canlii.org/en/ca/scc/",
            last_verified=_VERIFIED_ON,
            applies_to=["privilege", "evidence", "solicitor_client"],
            jurisdiction_scope=JurisdictionScope.CANADA,
            status=AuthorityStatus.VERIFIED,
        ),
        Citation(
            citation_id="CIT-2019-SCC-65",
            type=CitationType.CASE_LAW,
            jurisdiction="Canada",
            case_name="Canada (Minister of Citizenship and Immigration) v. Vavilov",
            citation="2019 SCC 65",
            neutral_citation="2019 SCC 65",
            short_cite="2019 SCC 65",
            principle_established="Reasonableness as the presumptive standard of review",
            parenthetical="Vavilov framework for JR",
            last_verified=_VERIFIED_ON,
            applies_to=["judicial_review", "standard_of_review"],
            jurisdiction_scope=JurisdictionScope.CANADA,
            status=AuthorityStatus.VERIFIED,
        ),
        Citation(
            citation_id="CIT-FAKE-UNVERIFIED",
            type=CitationType.CASE_LAW,
            jurisdiction="BC",
            case_name="Fake v. Imaginary",
            citation="2099 BCSC 1",
            short_cite="Fake v Imaginary",
            status=AuthorityStatus.UNVERIFIED,
            applies_to=[],
            jurisdiction_scope=JurisdictionScope.BC,
        ),
    ]
    for c in seeds:
        db.upsert(c, persist=False)
    if db.path:
        db.save()
    return db
