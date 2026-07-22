"""Create Phase 4 GitHub labels via gh CLI (requires: gh auth login)."""

from __future__ import annotations

import subprocess
import sys

LABELS: list[tuple[str, str, str]] = [
    ("area:security", "B60205", "Security workstream"),
    ("area:identity", "D93F0B", "Identity / auth"),
    ("area:matters", "FBCA04", "Matter isolation"),
    ("area:conflicts", "F9D0C4", "Conflict checking"),
    ("area:consent", "C5DEF5", "Consent ledger"),
    ("area:privilege", "0052CC", "Privilege engine"),
    ("area:ingestion", "5319E7", "Document ingestion"),
    ("area:ocr", "BFDADC", "OCR"),
    ("area:evidence", "0E8A16", "Evidence matrix"),
    ("area:knowledge", "006B75", "Legal knowledge"),
    ("area:legal-tests", "1D76DB", "Legal tests"),
    ("area:hitl", "E99695", "HITL"),
    ("area:deadlines", "D4C5F9", "Deadlines"),
    ("area:post-resolution", "C2E0C6", "Post-resolution"),
    ("area:client-portal", "FEF2C0", "Client portal"),
    ("area:windows", "BFD4F2", "Windows connector"),
    ("area:devops", "D93F0B", "DevOps"),
    ("area:testing", "FBCA04", "Testing"),
    ("area:compliance", "B60205", "Compliance"),
    ("type:epic", "3E4B9E", "Epic"),
    ("type:feature", "0E8A16", "Feature"),
    ("type:bug", "D73A4A", "Bug"),
    ("type:security", "B60205", "Security issue"),
    ("type:legal-review", "5319E7", "Legal review"),
    ("type:test", "FBCA04", "Test work"),
    ("type:documentation", "0075CA", "Docs"),
    ("type:infrastructure", "BFD4F2", "Infrastructure"),
    ("priority:P0-critical", "B60205", "Blocking"),
    ("priority:P1-high", "D93F0B", "High"),
    ("priority:P2-medium", "FBCA04", "Medium"),
    ("priority:P3-later", "C2E0C6", "Later"),
    ("status:blocked", "B60205", "Blocked"),
    ("status:ready", "0E8A16", "Ready"),
    ("status:in-progress", "1D76DB", "In progress"),
    ("status:human-review", "FBCA04", "Human review"),
    ("status:legal-review", "5319E7", "Legal review"),
    ("status:security-review", "B60205", "Security review"),
    ("status:completed", "0E8A16", "Completed"),
    ("risk:privilege", "B60205", "Privilege risk"),
    ("risk:confidentiality", "D93F0B", "Confidentiality risk"),
    ("risk:deadline", "FBCA04", "Deadline risk"),
    ("risk:legal-accuracy", "5319E7", "Legal accuracy"),
    ("risk:cross-matter", "B60205", "Cross-matter leak risk"),
    ("risk:data-loss", "D93F0B", "Data loss"),
    ("risk:unauthorized-practice", "B60205", "UPL risk"),
]


def main() -> int:
    try:
        subprocess.run(["gh", "auth", "status"], check=True, capture_output=True)
    except Exception:
        print("gh is not authenticated. Run: gh auth login", file=sys.stderr)
        return 1
    for name, color, desc in LABELS:
        subprocess.run(
            [
                "gh",
                "label",
                "create",
                name,
                "--color",
                color,
                "--description",
                desc,
                "--force",
            ],
            check=False,
        )
        print(f"label: {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
