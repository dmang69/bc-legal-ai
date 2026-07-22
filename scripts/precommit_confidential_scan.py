#!/usr/bin/env python3
"""Pre-commit entrypoint for confidential scan (M0-006)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SCAN = Path(__file__).with_name("scan_confidential.py")
_spec = importlib.util.spec_from_file_location("scan_confidential", _SCAN)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

if __name__ == "__main__":
    raise SystemExit(_mod.main())
