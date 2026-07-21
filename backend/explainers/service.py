"""Persist document explainers under matters/{id}/explainers/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from architecture.document_explainer import DocumentExplainer


def save_explainer(
    exp: DocumentExplainer,
    *,
    root: Optional[Path] = None,
) -> Path:
    if not exp.matter_id:
        raise ValueError("explainer.matter_id required")
    base = (root or Path("matters")).resolve()
    d = base / exp.matter_id / "explainers"
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{exp.explainer_id}.json"
    path.write_text(
        json.dumps(exp.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    md = d / f"{exp.explainer_id}.md"
    md.write_text(exp.format_explainer(), encoding="utf-8")
    return path


def load_explainer(
    matter_id: str,
    explainer_id: str,
    *,
    root: Optional[Path] = None,
) -> DocumentExplainer:
    base = (root or Path("matters")).resolve()
    path = base / matter_id / "explainers" / f"{explainer_id}.json"
    return DocumentExplainer.from_dict(json.loads(path.read_text(encoding="utf-8")))
