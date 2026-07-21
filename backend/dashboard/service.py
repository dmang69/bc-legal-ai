"""Persist case dashboards under matters/{id}/dashboard.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from architecture.case_status import CaseDashboard


def save_dashboard(
    dash: CaseDashboard,
    *,
    root: Optional[Path] = None,
) -> Path:
    if not dash.matter_id:
        raise ValueError("dashboard.matter_id required")
    base = (root or Path("matters")).resolve()
    d = base / dash.matter_id
    d.mkdir(parents=True, exist_ok=True)
    path = d / "dashboard.json"
    path.write_text(
        json.dumps(dash.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    md = d / "dashboard.md"
    md.write_text(dash.format_dashboard(), encoding="utf-8")
    return path


def load_dashboard(
    matter_id: str,
    *,
    root: Optional[Path] = None,
) -> CaseDashboard:
    base = (root or Path("matters")).resolve()
    path = base / matter_id / "dashboard.json"
    return CaseDashboard.from_dict(json.loads(path.read_text(encoding="utf-8")))
