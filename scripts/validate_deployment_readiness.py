"""
Deployment readiness gate for GitHub / Hugging Face publication.

This script does not upload or publish anything. It verifies that the repository
is in a safe state for a public-demo release and that local validation commands
needed before deployment succeed.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def _run(command: list[str], *, cwd: Path = ROOT, timeout: int = 120) -> CheckResult:
    try:
        proc = subprocess.run(
            command,
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - defensive CLI guard
        return CheckResult(" ".join(command), False, str(exc))
    return CheckResult(" ".join(command), proc.returncode == 0, proc.stdout.strip()[-4000:])


def check_public_environment() -> CheckResult:
    env = os.environ.copy()
    env.setdefault("APP_MODE", "public_demo")
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "from backend.api.public_demo import assert_public_deployment_safe, public_deployment_safety; "
            "assert_public_deployment_safe(); print(public_deployment_safety())",
        ],
        cwd=str(ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return CheckResult("public deployment environment", proc.returncode == 0, proc.stdout.strip())


def check_hf_assets() -> CheckResult:
    return _run([sys.executable, "scripts/validate-huggingface-assets.py"])


def check_backend_tests() -> CheckResult:
    return _run([sys.executable, "-m", "pytest"], timeout=180)


def check_frontend_build() -> CheckResult:
    npm = "npm.cmd" if os.name == "nt" else "npm"
    return _run([npm, "run", "build"], cwd=ROOT / "apps" / "platform-ui", timeout=180)


def run_checks(*, include_slow: bool) -> list[CheckResult]:
    checks = [check_public_environment(), check_hf_assets()]
    if include_slow:
        checks.extend([check_backend_tests(), check_frontend_build()])
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate deployment readiness without publishing.")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full backend tests and frontend production build in addition to fast safety checks.",
    )
    args = parser.parse_args()

    results = run_checks(include_slow=args.full)
    failed = [result for result in results if not result.ok]
    for result in results:
        status = "PASS" if result.ok else "FAIL"
        print(f"[{status}] {result.name}")
        if result.detail:
            print(result.detail)
            print()
    if failed:
        print("Deployment readiness FAILED; do not publish.")
        return 1
    print("Deployment readiness passed. Publication still requires human approval and credentials.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
