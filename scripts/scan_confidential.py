"""
Scan repository text for likely live-matter / confidential patterns.

Exit 1 if hits found (for CI / pre-commit). Not a substitute for human review.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Patterns that should not appear in public branches (except this scanner / SECURITY docs)
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("live_court_file", re.compile(r"KAM-S-S-\d{5}", re.I)),
    ("party_sanghera", re.compile(r"\bSanghera\b")),
    ("party_gurmail", re.compile(r"\bGurmail\b")),
    ("hf_token", re.compile(r"\bhf_[A-Za-z0-9]{20,}\b")),
]

SKIP_DIR_NAMES = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    ".hf-cli",
    "outputs",
    "matters",  # local gitignored client matters
}

# Allowlisted relative paths (docs explaining the scrub / scanner itself)
ALLOWLIST = {
    "scripts/scan_confidential.py",
    "SECURITY.md",
    "PRODUCT_STATUS.md",
    "architecture/AUDIT_P0_2026-07-21.md",
}

# Tests may assert absence of live markers (string must appear in source)
ALLOWLIST_PREFIXES = (
    "tests/",
)


def main() -> int:
    hits: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(p in SKIP_DIR_NAMES for p in path.parts):
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in ALLOWLIST or any(rel.startswith(p) for p in ALLOWLIST_PREFIXES):
            continue
        if path.suffix.lower() not in {
            ".py",
            ".md",
            ".txt",
            ".json",
            ".yml",
            ".yaml",
            ".csv",
            ".toml",
        }:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for label, pat in PATTERNS:
            if pat.search(text):
                hits.append(f"{rel}: {label}")
    if hits:
        print("CONFIDENTIAL / LIVE-MATTER PATTERN HITS:")
        for h in hits:
            print(f"  {h}")
        print(
            "\nRemove live matter data from public tree. "
            "Rewrite git history if previously pushed. See SECURITY.md."
        )
        return 1
    print("scan_confidential: OK (no blocked patterns in scanned files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
