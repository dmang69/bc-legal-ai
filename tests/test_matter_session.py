"""Matter session orchestration tests."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.matters import MatterSession, create_matter


def test_create_ingest_analyze_gate():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        s = create_matter(
            "Test matter",
            matter_id="m-test-1",
            root=root,
            parties=["T", "L"],
        )
        s.update(claimed_tags=["mold_hazard", "retaliatory_eviction"])
        s.ingest_file(
            "20251128_mold.jpg",
            b"bytes",
            human_notes="mold photo",
            location="990A",
        )
        report = s.analysis_report()
        assert report["summary"]["count"] == 1
        assert "retaliatory_eviction" in report["gaps"]
        assert "mold_hazard" not in report["gaps"]
        skeletons = s.draft_argument_skeletons()
        assert any(sk["claim"].endswith("mold_hazard") for sk in skeletons)
        path = s.write_report()
        assert path.is_file()
        # reload
        s2 = MatterSession("m-test-1", root=root)
        assert s2.meta.title == "Test matter"
        assert len(s2.matrix.all()) == 1


def test_privileged_ingest_blocks_export():
    with tempfile.TemporaryDirectory() as tmp:
        s = create_matter("Priv", matter_id="m-priv", root=Path(tmp))
        s.ingest_file(
            "advice.eml",
            b"secret advice",
            is_client_lawyer_comm=True,
            privilege_owner="client-1",
        )
        d = s.production_check(destination="opposing")
        assert d.allowed is False


if __name__ == "__main__":
    test_create_ingest_analyze_gate()
    test_privileged_ingest_blocks_export()
    print("OK: 2 matter session tests passed")
