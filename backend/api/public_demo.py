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


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def public_deployment_safety() -> dict[str, Any]:
    """Return fail-closed public deployment invariants for health checks and CI."""
    mode = app_mode()
    public = is_public_demo()
    uploads_enabled = _env_bool("ALLOW_PUBLIC_UPLOADS", False)
    client_data_enabled = _env_bool("ALLOW_CLIENT_DATA", False)
    court_ready_enabled = _env_bool("ALLOW_COURT_READY_EXPORTS", False)
    persistence_enabled = _env_bool("ALLOW_PUBLIC_PERSISTENCE", False)
    external_connectors_enabled = _env_bool("ALLOW_PUBLIC_CONNECTORS", False)
    violations: list[str] = []
    if public:
        if uploads_enabled:
            violations.append("ALLOW_PUBLIC_UPLOADS must be false in public_demo")
        if client_data_enabled:
            violations.append("ALLOW_CLIENT_DATA must be false in public_demo")
        if court_ready_enabled:
            violations.append("ALLOW_COURT_READY_EXPORTS must be false in public_demo")
        if persistence_enabled:
            violations.append("ALLOW_PUBLIC_PERSISTENCE must be false in public_demo")
        if external_connectors_enabled:
            violations.append("ALLOW_PUBLIC_CONNECTORS must be false in public_demo")
    return {
        "app_mode": mode,
        "public_demo": public,
        "allow_public_uploads": uploads_enabled,
        "allow_client_data": client_data_enabled,
        "allow_court_ready_exports": court_ready_enabled,
        "allow_public_persistence": persistence_enabled,
        "allow_public_connectors": external_connectors_enabled,
        "court_ready_forced_false": public and not court_ready_enabled,
        "synthetic_only": public and not client_data_enabled,
        "safe": not violations,
        "violations": violations,
    }


def assert_public_deployment_safe() -> None:
    safety = public_deployment_safety()
    if safety["public_demo"] and not safety["safe"]:
        raise RuntimeError("Unsafe public deployment configuration: " + "; ".join(safety["violations"]))


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
