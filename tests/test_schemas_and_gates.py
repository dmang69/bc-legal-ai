"""Foundation tests — citation gate and human approval (not a full legal suite)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.supervisor_gate import finalize_package, require_approval
from agents.verifier import assert_court_ready, gate_summary
from architecture.schemas import (
    ApprovalAction,
    AuthorityRecord,
    AuthorityStatus,
    Classification,
    Proposition,
    ReviewReport,
    VerificationStatus,
    court_ready_allowed,
)


def test_proposition_provenance_shape():
    p = Proposition(
        proposition="The arbitrator amended the address before the tenant joined.",
        classification=Classification.FACT,
        source_document="hearing-transcript.pdf",
        page=4,
        timestamp="00:04:36",
        confidence=0.98,
        verification_status=VerificationStatus.RECORD_SUPPORTED,
    )
    d = p.to_dict()
    assert d["classification"] == "FACT"
    assert d["page"] == 4
    assert d["timestamp"] == "00:04:36"
    assert d["verification_status"] == "record-supported"


def test_court_ready_blocks_unverified():
    authorities = [
        AuthorityRecord(
            official_title="Fake v Imaginary",
            jurisdiction="BC",
            neutral_citation="2020 BCSC 99999",
            status=AuthorityStatus.UNVERIFIED,
        )
    ]
    ok, blockers = court_ready_allowed(authorities)
    assert ok is False
    assert any("UNVERIFIED" in b for b in blockers)
    summary = gate_summary(authorities)
    assert summary["court_ready_allowed"] is False


def test_court_ready_allows_verified_only():
    authorities = [
        AuthorityRecord(
            official_title="Canada (Minister of Citizenship and Immigration) v. Vavilov",
            jurisdiction="Canada",
            court_or_tribunal="SCC",
            neutral_citation="2019 SCC 65",
            status=AuthorityStatus.VERIFIED,
            remains_current=True,
        )
    ]
    ok, blockers = court_ready_allowed(authorities)
    assert ok is True
    assert blockers == []
    assert_court_ready(authorities)  # no raise


def test_supervisor_requires_approval():
    try:
        require_approval(ApprovalAction.FILE_WITH_COURT, approved=False)
        raised = False
    except PermissionError:
        raised = True
    assert raised is True
    require_approval(ApprovalAction.FILE_WITH_COURT, approved=True)


def test_finalize_requires_human_and_clean_cites():
    report = ReviewReport(
        facts_checked=(43, 46),
        unsupported_factual_statements=3,
        authorities_verified=(18, 20),
        unverified_authorities=2,
        quotes_checked=(11, 11),
        deadlines_checked=(4, 5),
        cross_references_checked=(36, 36),
    )
    try:
        finalize_package(report, authorities_clean=False, human_approved=False)
        raised = False
    except PermissionError:
        raised = True
    assert raised is True

    clean = ReviewReport(
        facts_checked=(46, 46),
        unsupported_factual_statements=0,
        authorities_verified=(20, 20),
        unverified_authorities=0,
        quotes_checked=(11, 11),
        deadlines_checked=(5, 5),
        cross_references_checked=(36, 36),
    )
    out = finalize_package(clean, authorities_clean=True, human_approved=True)
    assert out.human_approval == "APPROVED"
    assert "Human approval:" in out.format()


if __name__ == "__main__":
    test_proposition_provenance_shape()
    test_court_ready_blocks_unverified()
    test_court_ready_allows_verified_only()
    test_supervisor_requires_approval()
    test_finalize_requires_human_and_clean_cites()
    print("OK: 5 foundation tests passed")
