"""
Local demo: create a matter, ingest sample (non-confidential) stubs, print analysis.

  python scripts/matter_demo.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.matters import create_matter


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        session = create_matter(
            "Demo mold / notice matter (synthetic)",
            matter_id="demo-synthetic",
            root=root,
            parties=["Tenant A", "Landlord B"],
            tribunal_or_court="RTB",
        )
        session.update(claimed_tags=["mold_hazard", "non_repair", "retaliatory_eviction"])

        session.ingest_file(
            "20231115_mold.jpg",
            b"fake-jpeg-bytes-2023",
            human_notes="back unit mold first documented",
            location="Unit 990A",
        )
        session.ingest_file(
            "20251128_084839.jpg",
            b"fake-jpeg-bytes-2025-still-mold",
            human_notes="ongoing mold after claimed repair",
            location="Unit 990A",
        )
        session.ingest_text(
            "notice_two_month.txt",
            "Two month notice for landlord use served after repair complaints.",
        )
        session.ingest_text(
            "city_fine_note.txt",
            "City bylaw inspection fine related to mould hazard.",
        )

        path = session.write_report()
        report = json.loads(path.read_text(encoding="utf-8"))
        print("=== Matter analysis (synthetic demo) ===")
        print(f"matter_id: {report['matter_id']}")
        print(f"summary: {report['summary']}")
        print(f"gaps: {report['gaps']}")
        print(f"temporal_conflicts: {len(report['temporal_conflicts'])}")
        print(f"privilege_gated: {report['privilege_gated_ids']}")
        print()
        print(report["chronology_markdown"])
        print()
        gate = session.production_check(destination="export")
        print(f"production_gate allowed={gate.allowed} reasons={gate.reasons[:3]}")
        print(f"report written: {path}")
        print("OK")


if __name__ == "__main__":
    main()
