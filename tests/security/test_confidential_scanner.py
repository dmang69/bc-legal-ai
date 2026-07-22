"""Tests for M0-005 confidential-data scanner."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN = ROOT / "scripts" / "scan_confidential.py"


def test_scanner_exits_zero_on_clean_repo():
    r = subprocess.run(
        [sys.executable, str(SCAN)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OK" in r.stdout


def test_pattern_rules_block_live_and_allow_noise():
    import re

    # Mirror config/confidential_patterns.yml critical rules (no PyYAML required)
    kam = re.compile(r"KAM-S-S-\d{5}", re.I)
    party = re.compile(r"\bSanghera\b")
    postal = re.compile(
        r"\b[ABCEGHJ-NPRSTVXY]\d[ABCEGHJ-NPRSTV-Z][ -]\d[ABCEGHJ-NPRSTV-Z]\d\b", re.I
    )
    phone = re.compile(
        r"(?:\+1[-.\s]|\(\d{3}\)[-.\s]?)\d{3}[-.\s]?\d{4}"
        r"|\b(?!000)(?!111)\d{3}[-.\s]\d{3}[-.\s]\d{4}\b"
    )
    assert kam.search("See file KAM-S-S-12345")
    assert party.search("Sanghera Holdings")
    assert not postal.search("color C2E0C6 is fine")
    assert postal.search("V6B 1A1")
    assert not phone.search("0000000000 65535 f")
    assert phone.search("604-555-0100")
