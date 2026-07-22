"""UNVERIFIED CITATION FLAG — options for missing/unverified authorities."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.grounding import (
    Citation,
    GroundedClaim,
    GroundingRefusalReason,
    InferenceStep,
)
from backend.grounding.citation_db import CitationDB, seed_bc_workbench_citations
from backend.grounding.gate import GroundingGate, flag_unverified_reference


def test_flag_not_in_database():
    db = seed_bc_workbench_citations(CitationDB())
    flag = flag_unverified_reference(db, "Smith v Jones 2099 BCSC 999")
    assert flag.in_database is False
    assert flag.court_ready_allowed is False
    assert flag.allows_illustrative_output is True
    text = flag.format_text()
    assert "UNVERIFIED CITATION FLAG" in text
    assert "does not exist in the verified citation database" in text
    assert "Add to database" in text
    assert "illustrative only" in text
    assert "equivalent verified citation" in text
    assert len(flag.options) == 3


def test_flag_partially_verified_in_db():
    db = seed_bc_workbench_citations(CitationDB())
    flag = flag_unverified_reference(db, Citation(citation_id="CIT-RTA-S56"))
    assert flag.in_database is True
    # P0: s.56 mis-use for retaliation → REJECTED (not PARTIALLY_VERIFIED)
    assert flag.database_status == "REJECTED"
    assert flag.citation_id == "CIT-RTA-S56"
    # equivalents for retaliatory may be empty if only S56 has that tag;
    # mold path should still suggest s.32 when referencing repair
    flag2 = flag_unverified_reference(db, "RTA s. 99 (fake)")
    assert flag2.in_database is False


def test_gate_includes_flag_on_refuse():
    db = seed_bc_workbench_citations(CitationDB())
    g = GroundingGate(known_node_ids=["EV-1"], citation_db=db)
    r = g.evaluate(
        GroundedClaim(
            claim="Argument relying on unknown case",
            factual_basis="EV-1",
            legal_basis=Citation(short_cite="Unknown v Nowhere 2020 BCSC 1"),
            inference_chain=[
                InferenceStep(statement="f", premise_type="fact", supports_from=["EV-1"]),
                InferenceStep(statement="law", premise_type="law"),
                InferenceStep(statement="therefore", premise_type="conclusion"),
            ],
        )
    )
    assert r.allowed is False
    assert GroundingRefusalReason.UNVERIFIED_CITATION in r.reasons
    assert r.unverified_citation_flag is not None
    assert r.illustrative_allowed is True
    refuse = r.refuse_text()
    assert "UNVERIFIED CITATION FLAG" in refuse
    assert "Options:" in refuse
    d = r.to_dict()
    assert d["unverified_citation_flag"]["flag"] == "UNVERIFIED_CITATION"
    assert len(d["unverified_citation_flag"]["options"]) == 3


def test_check_citation_none_when_verified():
    db = seed_bc_workbench_citations(CitationDB())
    g = GroundingGate(known_node_ids=["EV-1"], citation_db=db)
    assert g.check_citation("RTA s. 32") is None
    assert g.check_citation("Fake v Imaginary") is not None


def test_equivalents_for_privilege_hint():
    db = seed_bc_workbench_citations(CitationDB())
    flag = flag_unverified_reference(db, "some privilege case not in db")
    # should suggest Descoteaux via applies_to privilege
    ids = {e.get("citation_id") for e in flag.equivalent_candidates}
    assert "CIT-DESC-MIERZ" in ids or any(
        "Descoteaux" in (e.get("short_cite") or "") for e in flag.equivalent_candidates
    )


if __name__ == "__main__":
    test_flag_not_in_database()
    test_flag_partially_verified_in_db()
    test_gate_includes_flag_on_refuse()
    test_check_citation_none_when_verified()
    test_equivalents_for_privilege_hint()
    print("OK: 5 unverified citation flag tests passed")
