"""Grok-inspired live research — bounded public web fetch.

Fail-closed: disabled unless ALA_WEB_RESEARCH=1. Never send matter-confidential
content. Official law still prefers BC Laws fetcher, not generic web scrapes.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import quote_plus, urlparse


ALLOWED_HOST_SUFFIXES = (
    "bclaws.gov.bc.ca",
    "canlii.org",
    "gov.bc.ca",
    "canada.ca",
    "scc-csc.ca",
    "wikipedia.org",
    "github.com",
    "docs.python.org",
    "developer.mozilla.org",
)


@dataclass
class WebResearchResult:
    ok: bool
    query: str
    results: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""
    live: bool = False
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "query": self.query,
            "results": self.results,
            "error": self.error,
            "live": self.live,
            "warnings": self.warnings,
            "court_ready": False,
        }


def web_research_enabled() -> bool:
    return os.environ.get("ALA_WEB_RESEARCH", "").strip().lower() in ("1", "true", "yes")


def _host_allowed(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == s or host.endswith("." + s) for s in ALLOWED_HOST_SUFFIXES)


def research(query: str, *, max_results: int = 5) -> WebResearchResult:
    q = (query or "").strip()
    warnings = [
        "Web research is not a substitute for official BC Laws verification.",
        "Do not paste confidential client content into live research.",
        "court_ready: false",
    ]
    if not q:
        return WebResearchResult(False, q, error="Empty query", warnings=warnings)

    if not web_research_enabled():
        # Deterministic offline research card with official links
        results = [
            {
                "title": "BC Laws — official legislation",
                "url": "https://www.bclaws.gov.bc.ca/",
                "snippet": "Primary source for BC statutes and regulations. Check currency line.",
                "source": "curated",
            },
            {
                "title": "CanLII — case law index",
                "url": "https://www.canlii.org/en/bc/",
                "snippet": "Public case law database. Verify treatment and pinpoints.",
                "source": "curated",
            },
            {
                "title": "Query (offline mode)",
                "url": "",
                "snippet": f"Live web disabled. Query was: {q[:300]}. Set ALA_WEB_RESEARCH=1 to enable bounded live fetch.",
                "source": "local",
            },
        ]
        return WebResearchResult(True, q, results=results, live=False, warnings=warnings)

    try:
        import httpx
    except ImportError:
        return WebResearchResult(False, q, error="httpx not installed", warnings=warnings)

    # DuckDuckGo HTML lite (no API key) — best-effort; parse titles/links
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(q)}"
    try:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            r = client.get(url, headers={"User-Agent": "BC-Legal-AI-Research/0.3"})
            r.raise_for_status()
            html = r.text
    except Exception as e:
        return WebResearchResult(False, q, error=f"live fetch failed: {e}", warnings=warnings)

    links = re.findall(
        r'uddg=([^&"]+).*?class="result__a"[^>]*>(.*?)</a>',
        html,
        re.I | re.S,
    )
    results: list[dict[str, Any]] = []
    from urllib.parse import unquote

    for raw_u, title in links:
        u = unquote(raw_u)
        if not u.startswith("http"):
            continue
        if not _host_allowed(u):
            continue
        title_clean = re.sub(r"<[^>]+>", "", title).strip()
        results.append(
            {
                "title": title_clean[:200],
                "url": u,
                "snippet": "",
                "source": "live_filtered",
            }
        )
        if len(results) >= max_results:
            break

    if not results:
        warnings.append("No allowlisted hosts in live results; returning curated official links.")
        return WebResearchResult(
            True,
            q,
            results=[
                {
                    "title": "BC Laws — official legislation",
                    "url": "https://www.bclaws.gov.bc.ca/",
                    "snippet": "Primary source for BC statutes. Check currency line.",
                    "source": "curated_fallback",
                },
                {
                    "title": "CanLII BC",
                    "url": "https://www.canlii.org/en/bc/",
                    "snippet": "Public case law index.",
                    "source": "curated_fallback",
                },
            ],
            live=True,
            warnings=warnings,
        )
    return WebResearchResult(True, q, results=results, live=True, warnings=warnings)
