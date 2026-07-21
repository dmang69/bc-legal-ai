"""Persist petition outlines under matters/{id}/petition/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from architecture.petition import PetitionOutline


def _dir(root: Path, matter_id: str) -> Path:
    return root / matter_id / "petition"


def save_petition(
    outline: PetitionOutline,
    *,
    root: Optional[Path] = None,
) -> Path:
    if not outline.matter_id:
        raise ValueError("outline.matter_id required")
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


def load_petition(
    matter_id: str,
    outline_id: str,
    *,
    root: Optional[Path] = None,
) -> PetitionOutline:
    base = (root or Path("matters")).resolve()
    path = _dir(base, matter_id) / f"{outline_id}.json"
    return PetitionOutline.from_dict(
        json.loads(path.read_text(encoding="utf-8"))
    )


def list_petitions(matter_id: str, *, root: Optional[Path] = None) -> list[str]:
    base = (root or Path("matters")).resolve()
    d = _dir(base, matter_id)
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.json"))
