"""GroundingGate — refuse ungrounded claims."""

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
from architecture.schemas import AuthorityStatus
from backend.grounding.citation_db import CitationDB, seed_bc_workbench_citations
from backend.grounding.gate import GroundingGate


def _gate() -> GroundingGate:
    db = seed_bc_workbench_citations(CitationDB())
    return GroundingGate(
        known_node_ids=["EV-2026-000147", "EV-2026-000148"],
        citation_db=db,
    )


def test_refuse_missing_factual_basis():
    g = _gate()
    claim = GroundedClaim(
        claim="Mold was present in November 2025",
        factual_basis=None,
        legal_basis=Citation(short_cite="RTA s. 32", section="32"),
        inference_chain=[
            InferenceStep(statement="Photos show mold", premise_type="fact"),
            InferenceStep(statement="RTA requires repair", premise_type="law"),
            InferenceStep(statement="Therefore landlord obligations engaged", premise_type="conclusion"),
        ],
    )
    r = g.evaluate(claim)
    assert r.allowed is False
    assert GroundingRefusalReason.MISSING_FACTUAL_BASIS in r.reasons
    assert "No evidence supports this claim" in r.refuse_text()


def test_refuse_unknown_node_id():
    g = _gate()
    claim = GroundedClaim(
        claim="x",
        factual_basis="EV-MISSING",
        legal_basis=Citation(short_cite="RTA s. 32"),
        inference_chain=[
            InferenceStep(statement="a", premise_type="fact", supports_from=["EV-MISSING"]),
            InferenceStep(statement="b", premise_type="law"),
            InferenceStep(statement="therefore c", premise_type="conclusion"),
        ],
    )
    r = g.evaluate(claim)
    assert r.allowed is False
    assert GroundingRefusalReason.MISSING_FACTUAL_BASIS in r.reasons


def test_refuse_missing_legal_basis():
    g = _gate()
    claim = GroundedClaim(
        claim="Quiet enjoyment breached",
        factual_basis="EV-2026-000147",
        legal_basis=None,
        inference_chain=[
            InferenceStep(statement="Noise events", premise_type="fact", supports_from=["EV-2026-000147"]),
            InferenceStep(statement="therefore breach", premise_type="conclusion"),
        ],
    )
    r = g.evaluate(claim)
    assert r.allowed is False
    assert GroundingRefusalReason.MISSING_LEGAL_BASIS in r.reasons
    assert "No legal authority found" in " ".join(r.messages)


def test_refuse_unverified_citation():
    g = _gate()
    claim = GroundedClaim(
        claim="Something",
        factual_basis="EV-2026-000147",
        legal_basis=Citation(short_cite="Fake v Imaginary"),
        inference_chain=[
            InferenceStep(statement="fact", premise_type="fact", supports_from=["EV-2026-000147"]),
            InferenceStep(statement="law Fake v Imaginary", premise_type="law"),
            InferenceStep(statement="therefore x", premise_type="conclusion"),
        ],
    )
    r = g.evaluate(claim)
    assert r.allowed is False
    assert GroundingRefusalReason.UNVERIFIED_CITATION in r.reasons


def test_refuse_broken_inference_chain():
    g = _gate()
    claim = GroundedClaim(
        claim="Conclusion without steps",
        factual_basis="EV-2026-000147",
        legal_basis=Citation(short_cite="RTA s. 28", section="28"),
        inference_chain=[],
    )
    r = g.evaluate(claim)
    assert r.allowed is False
    assert GroundingRefusalReason.BROKEN_INFERENCE_CHAIN in r.reasons
    assert "Logical gap" in " ".join(r.messages)


def test_allow_fully_grounded_claim():
    g = _gate()
    claim = GroundedClaim(
        claim="Landlord failed to maintain premises free of mold",
        factual_basis="EV-2026-000147",
        legal_basis=Citation(short_cite="RTA s. 32", section="32"),
        inference_chain=[
            InferenceStep(
                statement="EV-2026-000147 shows mold present November 2025",
                premise_type="fact",
                supports_from=["EV-2026-000147"],
            ),
            InferenceStep(
                statement="RTA s. 32 requires repair and maintenance",
                premise_type="law",
            ),
            InferenceStep(
                statement="Therefore repair obligations are engaged on these facts",
                premise_type="conclusion",
            ),
        ],
    )
    r = g.evaluate(claim)
    assert r.allowed is True, r.messages
    assert r.grounded is not None
    assert r.grounded.legal_basis is not None
    assert r.grounded.legal_basis.status == AuthorityStatus.VERIFIED
    grounded = g.assert_grounded(claim)
    assert grounded.factual_basis == "EV-2026-000147"


def test_assert_grounded_raises():
    g = _gate()
    try:
        g.assert_grounded(GroundedClaim(claim="bare claim"))
        raised = False
    except PermissionError as e:
        raised = True
        assert "REFUSE_OUTPUT" in str(e)
    assert raised


if __name__ == "__main__":
    test_refuse_missing_factual_basis()
    test_refuse_unknown_node_id()
    test_refuse_missing_legal_basis()
    test_refuse_unverified_citation()
    test_refuse_broken_inference_chain()
    test_allow_fully_grounded_claim()
    test_assert_grounded_raises()
    print("OK: 7 grounding gate tests passed")
