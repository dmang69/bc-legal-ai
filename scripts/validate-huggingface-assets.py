"""
Validate Hugging Face assets before publishing.

Checks are intentionally conservative: public HF assets must not contain real
client/litigation data, secrets, or unsafe demo affordances.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPACE = ROOT / "huggingface-space"
HF = ROOT / "huggingface"

README_FILE = "README.md"
INDEX_FILE = "index.html"
STYLE_FILE = "style.css"
HF_CONFIG_FILE = "hf-assets.example.json"

REQUIRED_PATHS = [
    SPACE / README_FILE,
    SPACE / INDEX_FILE,
    SPACE / STYLE_FILE,
    HF / README_FILE,
    HF / "spaces" / README_FILE,
    HF / "datasets" / README_FILE,
    HF / "models" / README_FILE,
    HF / "buckets" / README_FILE,
    HF / "docs" / "SETUP.md",
    HF / "docs" / "PUBLISHING.md",
    HF / "docs" / "GOVERNANCE.md",
    HF / "config" / HF_CONFIG_FILE,
]

SECRET_PATTERNS = [
    re.compile(r"hf_[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
]

LIVE_MATTER_PATTERNS = [
    re.compile(r"\bKAM-S-S-\d{4,}\b", re.I),
    re.compile(r"\bVAN-S-S-\d{4,}\b", re.I),
    re.compile(r"\bRTB[-\s]\d{6,}\b", re.I),
    re.compile(r"\bRTB\s+(?:file|number)\s*[:#]?\s*\d{6,}\b", re.I),
]

REQUIRED_SPACE_TEXT = [
    "Not a lawyer",
    "Not legal advice",
    "Do not upload confidential",
    "public Space",
]

ASSET_ROOTS = (SPACE, HF)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def iter_asset_files() -> Iterable[Path]:
    for base in ASSET_ROOTS:
        if base.exists():
            yield from (path for path in base.rglob("*") if path.is_file())


def has_match(text: str, patterns: Iterable[re.Pattern[str]]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def is_allowed_synthetic_identifier(path: Path, text: str) -> bool:
    if "999999" not in text:
        return False
    return "synthetic" in text.lower() or "demo" in text.lower() or "example" in text.lower()


def check_required_paths(errors: list[str]) -> None:
    missing = [path for path in REQUIRED_PATHS if not path.exists()]
    errors.extend(f"Missing required HF asset file: {relative(path)}" for path in missing)


def check_patterns(
    errors: list[str],
    patterns: Iterable[re.Pattern[str]],
    message: str,
    *,
    allow_synthetic: bool = False,
) -> None:
    for path in iter_asset_files():
        text = read_text(path)
        if allow_synthetic and is_allowed_synthetic_identifier(path, text):
            continue
        if has_match(text, patterns):
            errors.append(f"{message} in {relative(path)}")


def check_no_secrets(errors: list[str]) -> None:
    check_patterns(errors, SECRET_PATTERNS, "Potential secret")


def check_no_live_matter_ids(errors: list[str]) -> None:
    check_patterns(
        errors,
        LIVE_MATTER_PATTERNS,
        "Potential live matter identifier",
        allow_synthetic=True,
    )


def check_space_disclaimer(errors: list[str]) -> None:
    combined = "\n".join(
        read_text(path) for path in (SPACE / README_FILE, SPACE / INDEX_FILE) if path.exists()
    ).lower()
    missing = [phrase for phrase in REQUIRED_SPACE_TEXT if phrase.lower() not in combined]
    errors.extend(f"Public Space missing required disclaimer phrase: {phrase}" for phrase in missing)


def check_space_sdk(errors: list[str]) -> None:
    readme = SPACE / README_FILE
    if readme.exists() and "sdk: static" not in read_text(readme):
        errors.append(f"{relative(readme)} should declare `sdk: static` for public demo")


def check_json_bool_false(data: dict, section: str, field: str, errors: list[str]) -> None:
    if data.get(section, {}).get(field) is not False:
        errors.append(f"HF config must set {section}.{field}=false")


def check_config(errors: list[str]) -> None:
    cfg = HF / "config" / HF_CONFIG_FILE
    if not cfg.exists():
        return
    try:
        data = json.loads(read_text(cfg))
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {relative(cfg)}: {exc}")
        return
    check_json_bool_false(data, "space", "allow_client_data", errors)
    check_json_bool_false(data, "dataset", "allow_client_data", errors)


def run_checks() -> list[str]:
    errors: list[str] = []
    checks = [
        check_required_paths,
        check_no_secrets,
        check_no_live_matter_ids,
        check_space_disclaimer,
        check_space_sdk,
        check_config,
    ]
    for check in checks:
        check(errors)
    return errors


def report_errors(errors: list[str]) -> int:
    print("HF asset validation FAILED:")
    for err in errors:
        print(f"- {err}")
    return 1


def main() -> int:
    errors = run_checks()
    if errors:
        return report_errors(errors)
    print("HF asset validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
