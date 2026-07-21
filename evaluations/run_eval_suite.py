"""
§7 success-criteria eval stubs (FINE_TUNING_DESIGNATION.md).

No model inference — structural checks only until LoRA exists.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.schemas import AuthorityRecord, AuthorityStatus, court_ready_allowed


def load_rta_regression() -> dict:
    path = Path(__file__).parent / "citation_tests" / "rta_section_regression.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_section_map_self_consistent() -> list[str]:
    """Correct pins must not appear in wrong_sections lists."""
    errors: list[str] = []
    data = load_rta_regression()
    for t in data["tests"]:
        if t["correct_section"] in t.get("wrong_sections", []):
            errors.append(f"{t['id']}: correct_section listed as wrong")
        if not t["correct_section"]:
            errors.append(f"{t['id']}: missing correct_section")
    return errors


def test_unverified_authority_blocked() -> list[str]:
    errors: list[str] = []
    bad = AuthorityRecord(
        official_title="Fake v Case",
        jurisdiction="BC",
        neutral_citation="2099 BCSC 1",
        status=AuthorityStatus.UNVERIFIED,
    )
    ok, blockers = court_ready_allowed([bad])
    if ok:
        errors.append("UNVERIFIED authority was allowed in court-ready mode")
    if not blockers:
        errors.append("expected blockers for UNVERIFIED")
    good = AuthorityRecord(
        official_title="Vavilov",
        jurisdiction="Canada",
        neutral_citation="2019 SCC 65",
        status=AuthorityStatus.VERIFIED,
    )
    ok2, _ = court_ready_allowed([good])
    if not ok2:
        errors.append("VERIFIED authority blocked incorrectly")
    return errors


def test_statute_metadata_required_shape() -> list[str]:
    """Training/inference chunks must carry mandatory metadata keys."""
    required = {
        "enactment",
        "citation",
        "bclaws_url",
        "currency_line",
        "accessed_on",
        "version_kind",
        "section_ids",
    }
    # Example compliant chunk (from designation)
    sample = {
        "enactment": "Residential Tenancy Act",
        "citation": "SBC 2002, c 78",
        "bclaws_url": "https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/02078_01",
        "currency_line": "current to July 14, 2026",
        "accessed_on": "2026-07-21",
        "version_kind": "current_consolidated",
        "event_date": None,
        "section_ids": ["28", "32"],
        "text": "[excerpt would go here from BC Laws only]",
    }
    missing = required - set(sample.keys())
    return [f"missing key {k}" for k in missing]


def test_quiet_enjoyment_not_s22() -> list[str]:
    data = load_rta_regression()
    qe = next(t for t in data["tests"] if t["id"] == "quiet_enjoyment")
    errors: list[str] = []
    if qe["correct_section"] != "28":
        errors.append("quiet enjoyment must be s. 28")
    if "22" not in qe["wrong_sections"]:
        errors.append("s. 22 must be listed as wrong pin for quiet enjoyment")
    return errors


def main() -> int:
    suites = [
        ("section_map", test_section_map_self_consistent),
        ("court_ready_gate", test_unverified_authority_blocked),
        ("statute_metadata", test_statute_metadata_required_shape),
        ("quiet_enjoyment_pin", test_quiet_enjoyment_not_s22),
    ]
    failed = 0
    for name, fn in suites:
        errs = fn()
        if errs:
            failed += 1
            print(f"FAIL {name}:")
            for e in errs:
                print(f"  - {e}")
        else:
            print(f"PASS {name}")
    print(f"\n{len(suites) - failed}/{len(suites)} eval suites passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
