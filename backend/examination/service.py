"""Persist examination outlines under matters/{id}/examination/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from architecture.examination import ExaminationOutline


def _dir(root: Path, matter_id: str) -> Path:
    return root / matter_id / "examination"


def save_outline(
    outline: ExaminationOutline,
    *,
    root: Optional[Path] = None,
) -> Path:
    if not outline.matter_id:
        raise ValueError("outline.matter_id required to save")
    base = (root or Path("matters")).resolve()
    d = _dir(base, outline.matter_id)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{outline.outline_id}.json"
    path.write_text(
        json.dumps(outline.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    md = d / f"{outline.outline_id}.md"
    md.write_text(outline.format_outline(), encoding="utf-8")
    return path


def load_outline(
    matter_id: str,
    outline_id: str,
    *,
    root: Optional[Path] = None,
) -> ExaminationOutline:
    base = (root or Path("matters")).resolve()
    path = _dir(base, matter_id) / f"{outline_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return ExaminationOutline.from_dict(data)


def list_outlines(matter_id: str, *, root: Optional[Path] = None) -> list[str]:
    base = (root or Path("matters")).resolve()
    d = _dir(base, matter_id)
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.json"))
