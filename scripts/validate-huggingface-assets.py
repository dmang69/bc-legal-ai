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
SKILLS = ROOT / "skills"

README_FILE = "README.md"
INDEX_FILE = "index.html"
STYLE_FILE = "style.css"
APP_FILE = "app.py"
REQ_FILE = "requirements.txt"
HF_CONFIG_FILE = "hf-assets.example.json"

REQUIRED_PATHS = [
    SPACE / README_FILE,
    SPACE / APP_FILE,
    SPACE / REQ_FILE,
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
    re.compile(r"\bRTB[ \t]+(?:file|number)[ \t]*[:#]?[ \t]*\d{6,}\b", re.I),
]

REQUIRED_SPACE_TEXT = [
    "Not a lawyer",
    "Not legal advice",
    "Do not upload confidential",
    "public Space",
]

ASSET_ROOTS = (SPACE, HF)
TENANCY_SKILL_ROOTS = (
    SKILLS / "bc-tenancy-substantive",
    SKILLS / "bc-tenancy-procedure",
    SKILLS / "bc-tenancy-advocacy",
)

FORBIDDEN_DEPLOYMENT_PATTERNS = [
    re.compile(r"trust_remote_code\s*=\s*True"),
    re.compile(r'"model_type"\s*:\s*"bc_legal_ai_policy_card"'),
]

# Match only affirmative stale propositions, not correction notes that explicitly
# say a mapping is wrong or prohibited.
FORBIDDEN_LEGAL_CLAIMS = [
    re.compile(r"(?i)\bs\.?\s*6\b[^\n|]{0,40}\bcannot contract out\b"),
    re.compile(r"(?i)\bs\.?\s*8\b[^\n|]{0,40}\bonly rent\b"),
    re.compile(r"(?i)\bs\.?\s*22\b[^\n|]{0,40}\bquiet enjoyment\b"),
    re.compile(r"(?i)\bss?\.?\s*25\s*[–-]\s*26\b[^\n|]{0,40}\bentry\b"),
    re.compile(r"(?i)\bs\.?\s*47\.1\b[^\n|]{0,40}\b(?:no retaliation|retaliatory action prohibited)\b"),
    re.compile(r"(?i)\bs\.?\s*51\.3\b[^\n|]{0,50}\bright of first refusal\b"),
]


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


def is_allowed_synthetic_identifier(text: str) -> bool:
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
        if allow_synthetic and is_allowed_synthetic_identifier(text):
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
    if readme.exists() and "sdk: gradio" not in read_text(readme):
        errors.append(f"{relative(readme)} should declare `sdk: gradio` for public demo")


def check_transformers_gate(errors: list[str]) -> None:
    app = SPACE / APP_FILE
    if not app.exists():
        return
    text = read_text(app)
    required = [
        'ENABLE_TRANSFORMERS_INFERENCE", "false"',
        'MODEL_REVISION = os.environ.get("HF_MODEL_REVISION"',
        "TRUST_REMOTE_CODE = False",
        'BLOCKED_MODEL_TYPES = {"bc_legal_ai_policy_card"}',
        "AutoConfig.from_pretrained",
        'if getattr(config, "auto_map", None)',
        "def safe_model_demo",
        "enforce_public_text(prompt)",
        "not legal advice; not court-ready",
    ]
    for marker in required:
        if marker not in text:
            errors.append(f"Optional Transformers inference gate missing marker `{marker}`")
    for pattern in FORBIDDEN_DEPLOYMENT_PATTERNS:
        if pattern.search(text):
            errors.append(f"Unsafe model deployment pattern `{pattern.pattern}` in {relative(app)}")


def check_space_metadata_and_requirements(errors: list[str]) -> None:
    readme = SPACE / README_FILE
    requirements = SPACE / REQ_FILE
    if not readme.exists() or not requirements.exists():
        return
    metadata = read_text(readme)
    deps = read_text(requirements)
    required_metadata = ["sdk: gradio", "sdk_version: 5.49.1", "app_file: app.py"]
    for marker in required_metadata:
        if marker not in metadata:
            errors.append(f"Space metadata missing `{marker}`")
    if "gradio==5.49.1" not in deps:
        errors.append("Space requirements must pin gradio==5.49.1 to match metadata")
    if "static" in metadata.lower():
        errors.append("Gradio Space README must not describe the active deployment as static")


def iter_tenancy_markdown() -> Iterable[Path]:
    for root in TENANCY_SKILL_ROOTS:
        if root.exists():
            yield from root.rglob("*.md")


def check_tenancy_legal_integrity(errors: list[str]) -> None:
    for path in iter_tenancy_markdown():
        for line_number, line in enumerate(read_text(path).splitlines(), 1):
            lowered = line.lower()
            if any(word in lowered for word in ("incorrect", "not ", "never", "correction", "wrong")):
                continue
            for pattern in FORBIDDEN_LEGAL_CLAIMS:
                if pattern.search(line):
                    errors.append(
                        f"Stale RTA mapping in {relative(path)}:{line_number}: `{line.strip()}`"
                    )


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
    if data.get("space", {}).get("sdk") != "gradio":
        errors.append("HF config must set space.sdk=gradio")
    if data.get("space", {}).get("sdk_version") != "5.49.1":
        errors.append("HF config must pin space.sdk_version=5.49.1")
    if data.get("space", {}).get("app_file") != "app.py":
        errors.append("HF config must set space.app_file=app.py")
    models = data.get("models", {})
    if models.get("publish_enabled") is not False:
        errors.append("HF config must keep models.publish_enabled=false until release gates pass")
    if models.get("inference_enabled_by_default") is not False:
        errors.append("HF config must keep model inference disabled by default")
    if models.get("trust_remote_code") is not False:
        errors.append("HF config must set models.trust_remote_code=false")
    if models.get("requires_pinned_revision") is not True:
        errors.append("HF config must require a pinned model revision")


def run_checks() -> list[str]:
    errors: list[str] = []
    checks = [
        check_required_paths,
        check_no_secrets,
        check_no_live_matter_ids,
        check_space_disclaimer,
        check_space_sdk,
        check_transformers_gate,
        check_space_metadata_and_requirements,
        check_tenancy_legal_integrity,
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
