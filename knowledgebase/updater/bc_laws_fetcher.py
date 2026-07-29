"""Fetch official statute HTML from BC Laws and record currency metadata.

Fail-closed: never invent statute text. Network failures return ok=False.
Public demos should not call this with client data; use for knowledge refresh only.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

# Official BC Laws host only
ALLOWED_HOSTS = {"www.bclaws.gov.bc.ca", "bclaws.gov.bc.ca"}

# Well-known official document IDs (complete consolidations)
KNOWN_STATUTES = {
    "RTA": {
        "title": "Residential Tenancy Act, SBC 2002, c 78",
        "url": "https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/02078_01",
        "citation": "SBC 2002, c 78",
    },
    "JRPA": {
        "title": "Judicial Review Procedure Act, RSBC 1996, c 241",
        "url": "https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/96241_01",
        "citation": "RSBC 1996, c 241",
    },
    "ATA": {
        "title": "Administrative Tribunals Act, SBC 2004, c 45",
        "url": "https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/04045_01",
        "citation": "SBC 2004, c 45",
    },
}

_CURRENCY_RE = re.compile(
    r"current\s+to\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2})",
    re.I,
)
_SECTION_RE = re.compile(
    r"(?:section|s\.)\s*(\d+[A-Za-z]?)",
    re.I,
)

_ROOT = Path(__file__).resolve().parents[2]
_SNAPSHOT_DIR = _ROOT / "data" / "bc_laws_snapshots"


@dataclass
class BcLawsFetchResult:
    ok: bool
    source_key: str
    title: str = ""
    official_url: str = ""
    citation: str = ""
    current_to: Optional[str] = None
    accessed: str = ""
    content_hash: str = ""
    content_chars: int = 0
    snapshot_path: str = ""
    error: str = ""
    court_ready: bool = False  # always False until human verifies currency
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "source_key": self.source_key,
            "title": self.title,
            "official_url": self.official_url,
            "citation": self.citation,
            "current_to": self.current_to,
            "accessed": self.accessed,
            "content_hash": self.content_hash,
            "content_chars": self.content_chars,
            "snapshot_path": self.snapshot_path,
            "error": self.error,
            "court_ready": self.court_ready,
            "warnings": self.warnings,
            "statute_source": "BC Laws only",
        }


def _assert_official_url(url: str) -> None:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host not in ALLOWED_HOSTS:
        raise ValueError(f"Refusing non-BC-Laws host: {host}")
    if parsed.scheme not in ("https", "http"):
        raise ValueError("URL scheme must be http(s)")


def extract_currency_line(html: str) -> Optional[str]:
    m = _CURRENCY_RE.search(html or "")
    if m:
        return m.group(1).strip()
    return None


def fetch_bc_laws(
    source_key: str = "RTA",
    *,
    url: Optional[str] = None,
    timeout: float = 30.0,
    persist: bool = True,
) -> BcLawsFetchResult:
    """HTTP GET official BC Laws page; optional local snapshot under data/."""
    accessed = datetime.now(timezone.utc).isoformat()
    meta = KNOWN_STATUTES.get(source_key.upper())
    if url:
        official = url
        title = source_key
        citation = ""
    elif meta:
        official = meta["url"]
        title = meta["title"]
        citation = meta["citation"]
    else:
        return BcLawsFetchResult(
            ok=False,
            source_key=source_key,
            error=f"Unknown source_key {source_key}; pass url= or use {list(KNOWN_STATUTES)}",
            accessed=accessed,
        )

    try:
        _assert_official_url(official)
    except ValueError as e:
        return BcLawsFetchResult(
            ok=False, source_key=source_key, error=str(e), accessed=accessed
        )

    if os.environ.get("ALA_BC_LAWS_OFFLINE", "").strip() in ("1", "true", "yes"):
        return BcLawsFetchResult(
            ok=False,
            source_key=source_key,
            title=title,
            official_url=official,
            citation=citation,
            accessed=accessed,
            error="ALA_BC_LAWS_OFFLINE set — network fetch disabled",
            warnings=["Use local legislation/ extracts or re-enable network"],
        )

    try:
        import httpx
    except ImportError:
        return BcLawsFetchResult(
            ok=False,
            source_key=source_key,
            official_url=official,
            accessed=accessed,
            error="httpx not installed",
        )

    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            r = client.get(official, headers={"User-Agent": "BC-Legal-AI-Associate/0.2 (research; not legal advice)"})
            r.raise_for_status()
            html = r.text
    except Exception as e:
        return BcLawsFetchResult(
            ok=False,
            source_key=source_key,
            title=title,
            official_url=official,
            citation=citation,
            accessed=accessed,
            error=f"fetch failed: {e}",
        )

    current_to = extract_currency_line(html)
    content_hash = hashlib.sha256(html.encode("utf-8", errors="replace")).hexdigest()
    warnings = []
    if not current_to:
        warnings.append("Currency line not detected — human must verify on BC Laws before reliance")

    snapshot_path = ""
    if persist:
        _SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        fname = f"{source_key.upper()}_{content_hash[:12]}.html"
        path = _SNAPSHOT_DIR / fname
        path.write_text(html, encoding="utf-8", errors="replace")
        snapshot_path = str(path)

    return BcLawsFetchResult(
        ok=True,
        source_key=source_key.upper(),
        title=title,
        official_url=official,
        citation=citation,
        current_to=current_to,
        accessed=accessed,
        content_hash=content_hash,
        content_chars=len(html),
        snapshot_path=snapshot_path,
        court_ready=False,  # never auto court-ready
        warnings=warnings
        + ["Not legal advice. Re-verify currency on BC Laws before any filing."],
    )


def section_pin_supported_in_html(html: str, section: str) -> bool:
    """Heuristic: section number appears in HTML (not a substitute for pin-cite)."""
    sec = section.strip().lstrip("sS.").strip()
    if not sec:
        return False
    return bool(re.search(rf"\b{re.escape(sec)}\b", html or ""))
