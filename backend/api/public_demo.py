"""
Public-demo environment guard (M0-E5).

APP_MODE=public_demo rejects uploads, persistent matters, connectors,
and court-ready exports.
"""

from __future__ import annotations

import os
import re
from typing import Any


def app_mode() -> str:
    return os.environ.get("APP_MODE", "development").strip().lower()


def is_public_demo() -> bool:
    return app_mode() in ("public_demo", "public", "hf_space", "demo")


_BLOCK_PATTERNS = [
    re.compile(r"\b[A-Z]{3}-S-S-\d{5,6}\b"),
    re.compile(r"\bRTB[-\s]?\d{6,}\b", re.I),
    re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),
]


def reject_if_public_demo(action: str) -> None:
    if is_public_demo():
        raise PermissionError(
            f"Rejected in APP_MODE=public_demo: {action}. "
            "Use synthetic fixtures only; real matters require private infrastructure."
        )


def scan_user_text_for_confidential(text: str) -> list[str]:
    hits: list[str] = []
    for pat in _BLOCK_PATTERNS:
        if pat.search(text or ""):
            hits.append(pat.pattern)
    return hits


def enforce_public_text(text: str) -> dict[str, Any]:
    """Return error payload if public demo text looks like live matter identifiers."""
    if not is_public_demo():
        return {"ok": True}
    hits = scan_user_text_for_confidential(text)
    if hits:
        return {
            "ok": False,
            "error": "Input appears to contain court/RTB/phone identifiers. "
            "Public demo accepts fictional scenarios only.",
            "patterns": hits,
        }
    return {"ok": True}


def synthetic_marker() -> dict[str, bool]:
    return {"synthetic": True, "public_demo_approved": True}
