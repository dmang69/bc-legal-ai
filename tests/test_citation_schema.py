"""Full Citation schema + registry."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.grounding import Citation, CitationType, JurisdictionScope
from architecture.schemas import AuthorityStatus
from backend.grounding.citation_db import CitationDB, seed_bc_workbench_citations
from backend.grounding.gate import GroundingGate
from architecture.grounding import GroundedClaim, InferenceStep, GroundingRefusalReason


def test_citation_shape_statute():
    c = Citation(
        citation_id="CIT-RTA-S56",
        type=CitationType.STATUTE,
        jurisdiction="BC",
        act="Residential Tenancy Act",
        section="56",
        subsection="1",
        exact_text=None,  # must be filled from BC Laws when verified for court use
        source_url="https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/02078_01",
        last_verified="2026-07-21",
        applies_to=["retaliatory_eviction"],
        jurisdiction_scope=JurisdictionScope.BC,
        status=AuthorityStatus.PARTIALLY_VERIFIED,
    )
    d = c.to_dict()
    for key in (
        "citation_id",
        "type",
        "jurisdiction",
        "act",
        "section",
        "subsection",
        "exact_text",
        "source_url",
        "last_verified",
        "verifying_hash",
        "superseded_by",
        "applies_to",
        "jurisdiction_scope",
        "status",
    ):
        assert key in d
    assert d["citation_id"] == "CIT-RTA-S56"
    assert d["type"] == "STATUTE"
    assert d["section"] == "56"


def test_citation_shape_case_law():
    c = Citation(
        type=CitationType.CASE_LAW,
        case_name="Descoteaux v. Mierzwinski",
        citation="[1982] 2 SCR 890",
        principle_established="Solicitor-client privilege belongs to client",
        parenthetical="privilege is client's right alone to waive",
        applies_to=["privilege", "evidence"],
        jurisdiction_scope=JurisdictionScope.CANADA,
        status=AuthorityStatus.VERIFIED,
        last_verified="2026-07-21",
    )
    d = c.to_dict()
    assert d["case_name"].startswith("Descoteaux")
    assert "SCR 890" in (d["citation"] or "")
    assert d["principle_established"]
    assert "privilege" in d["applies_to"]


def test_seed_resolve_and_applies_to():
    db = seed_bc_workbench_citations(CitationDB())
    hit = db.resolve(Citation(short_cite="RTA s. 32", section="32"))
    assert hit is not None
    assert hit.citation_id == "CIT-RTA-S32"
    assert hit.status == AuthorityStatus.VERIFIED
    mold = db.by_applies_to("mold_hazard")
    assert any(c.section == "32" for c in mold)
    desc = db.resolve(Citation(case_name="Descoteaux v. Mierzwinski"))
    assert desc is not None
    assert desc.principle_established


def test_partially_verified_rta_s56_refused_by_gate():
    db = seed_bc_workbench_citations(CitationDB())
    g = GroundingGate(known_node_ids=["EV-1"], citation_db=db)
    r = g.evaluate(
        GroundedClaim(
            claim="Retaliatory notice",
            factual_basis="EV-1",
            legal_basis=Citation(citation_id="CIT-RTA-S56"),
            inference_chain=[
                InferenceStep(statement="notice after complaint", premise_type="fact", supports_from=["EV-1"]),
                InferenceStep(statement="RTA s.56", premise_type="law"),
                InferenceStep(statement="therefore issue raised", premise_type="conclusion"),
            ],
        )
    )
    assert r.allowed is False
    # CIT-RTA-S56 is REJECTED for retaliation use (P0); either rejection path is correct
    assert (
        GroundingRefusalReason.UNVERIFIED_CITATION in r.reasons
        or GroundingRefusalReason.REJECTED_CITATION in r.reasons
    )


def test_superseded_refused():
    db = CitationDB()
    old = Citation(
        citation_id="CIT-OLD",
        short_cite="Old Act s.1",
        status=AuthorityStatus.VERIFIED,
        superseded_by="CIT-NEW",
    )
    new = Citation(
        citation_id="CIT-NEW",
        short_cite="New Act s.1",
        status=AuthorityStatus.VERIFIED,
    )
    db.upsert(old)
    db.upsert(new)
    g = GroundingGate(known_node_ids=["EV-1"], citation_db=db)
    r = g.evaluate(
        GroundedClaim(
            claim="x",
            factual_basis="EV-1",
            legal_basis=Citation(citation_id="CIT-OLD"),
            inference_chain=[
                InferenceStep(statement="f", premise_type="fact", supports_from=["EV-1"]),
                InferenceStep(statement="law", premise_type="law"),
                InferenceStep(statement="therefore", premise_type="conclusion"),
            ],
        )
    )
    assert r.allowed is False
    assert GroundingRefusalReason.SUPERSEDED_CITATION in r.reasons


if __name__ == "__main__":
    test_citation_shape_statute()
    test_citation_shape_case_law()
    test_seed_resolve_and_applies_to()
    test_partially_verified_rta_s56_refused_by_gate()
    test_superseded_refused()
    print("OK: 5 citation schema tests passed")
