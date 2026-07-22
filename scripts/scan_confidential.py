"""
Scan repository for confidential / live-matter patterns (M0-005).

Uses config/confidential_patterns.yml when present.
Exit 1 on hits. For CI and pre-commit.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "confidential_patterns.yml"

SKIP_DIR_NAMES = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    ".hf-cli",
    "outputs",
    "matters",
    "dist",
    "build",
    ".venv",
    "venv",
    "target",
}

DEFAULT_IGNORE_FILENAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "cargo.lock",
    "uv.lock",
}


def _load_config() -> tuple[
    list[tuple[str, re.Pattern[str]]],
    set[str],
    tuple[str, ...],
    set[str],
]:
    patterns: list[tuple[str, re.Pattern[str]]] = []
    allow: set[str] = set()
    prefixes: list[str] = ["tests/", "fixtures/synthetic/"]
    ignore_names = set(DEFAULT_IGNORE_FILENAMES)
    if CONFIG.is_file():
        try:
            import yaml  # type: ignore

            data = yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
        except Exception:
            data = _parse_yaml_lite(CONFIG.read_text(encoding="utf-8"))
        for p in data.get("patterns") or []:
            patterns.append((p["id"], re.compile(p["regex"], re.I)))
        allow = set(data.get("allowlist_paths") or [])
        prefixes = list(data.get("allowlist_prefixes") or prefixes)
        for name in data.get("ignore_filenames") or []:
            ignore_names.add(str(name).lower())
    else:
        patterns = [
            ("kam_live_file", re.compile(r"KAM-S-S-\d{5}", re.I)),
            ("party_sanghera", re.compile(r"\bSanghera\b")),
            ("hf_token", re.compile(r"\bhf_[A-Za-z0-9]{20,}\b")),
        ]
    return patterns, allow, tuple(prefixes), ignore_names


def _parse_yaml_lite(text: str) -> dict:
    """Minimal fallback if PyYAML not installed."""
    patterns = []
    allow: list[str] = []
    prefixes: list[str] = []
    ignore_filenames: list[str] = []
    mode = None
    cur: dict = {}
    for line in text.splitlines():
        if line.strip().startswith("- id:"):
            if cur.get("id") and cur.get("regex"):
                patterns.append(cur)
            cur = {"id": line.split(":", 1)[1].strip()}
        elif "regex:" in line and cur is not None:
            raw = line.split("regex:", 1)[1].strip().strip("'\"")
            cur["regex"] = raw
        elif line.strip().startswith("- ") and mode == "allow":
            allow.append(line.strip()[2:].strip())
        elif line.strip().startswith("- ") and mode == "prefix":
            prefixes.append(line.strip()[2:].strip())
        elif line.strip().startswith("- ") and mode == "ignore_fn":
            ignore_filenames.append(line.strip()[2:].strip())
        elif "allowlist_paths:" in line:
            mode = "allow"
        elif "allowlist_prefixes:" in line:
            mode = "prefix"
        elif "ignore_filenames:" in line:
            mode = "ignore_fn"
        elif line.startswith("patterns:"):
            mode = "patterns"
    if cur.get("id") and cur.get("regex"):
        patterns.append(cur)
    return {
        "patterns": patterns,
        "allowlist_paths": allow,
        "allowlist_prefixes": prefixes or ["tests/", "fixtures/synthetic/"],
        "ignore_filenames": ignore_filenames,
    }


def main() -> int:
    patterns, allow, prefixes, ignore_names = _load_config()
    compiled: list[tuple[str, re.Pattern[str]]] = []
    for item in patterns:
        if isinstance(item, tuple):
            compiled.append(item)
        else:
            compiled.append((item["id"], re.compile(item["regex"], re.I)))

    hits: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(p in SKIP_DIR_NAMES for p in path.parts):
            continue
        if path.name.lower() in ignore_names:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in allow or any(rel.startswith(p) for p in prefixes):
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
            ".html",
            ".js",
            ".css",
            ".ts",
            ".tsx",
        }:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if '"synthetic": true' in text and "public_demo_approved" in text:
            continue
        for label, pat in compiled:
            if pat.search(text):
                if label == "bc_court_file" and "999999" in text and "DEMO" in text.upper():
                    continue
                hits.append(f"{rel}: {label}")

    if hits:
        print("CONFIDENTIAL / LIVE-MATTER PATTERN HITS:")
        for h in sorted(set(hits)):
            print(f"  {h}")
        print("\nSee config/confidential_patterns.yml and SECURITY.md")
        return 1
    print("scan_confidential: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
