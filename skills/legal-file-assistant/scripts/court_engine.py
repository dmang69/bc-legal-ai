"""
Canadian court document downloader — lawful public sources only.

SCC: decisions.scc-csc.ca (direct PDF when item ID known).
CanLII / blocked BC: reference PDF + URL (no Cloudflare bypass).
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Verified SCC item IDs (see references/scc-item-ids.md)
SCC_ITEM_IDS: dict[str, dict[str, str]] = {
    "2019 SCC 65": {"name": "Vavilov", "item_id": "18078"},
    "2011 SCC 61": {"name": "Alberta Teachers", "item_id": "7979"},
    "2008 SCC 9": {"name": "Dunsmuir", "item_id": "5615"},
    "[1999] 2 SCR 817": {"name": "Baker", "item_id": "1717"},
    "1999 2 SCR 817": {"name": "Baker", "item_id": "1717"},
    "[1985] 2 SCR 643": {"name": "Cardinal", "item_id": "2697"},
    "[1978] 1 SCR 369": {"name": "Committee for Justice & Liberty", "item_id": "2265"},
    "[1979] 1 SCR 311": {"name": "Nicholson", "item_id": "2471"},
    "[1992] 1 SCR 623": {"name": "Newfoundland Telephone", "item_id": "1437"},
    "2001 SCC 52": {"name": "Ocean Port Hotel", "item_id": "5176"},
    "2017 SCC 23": {"name": "Pintea v. Johns", "item_id": "16589"},
    "2011 SCC 62": {"name": "Newfoundland Nurses", "item_id": "7980"},
    "2001 SCC 4": {"name": "Ellis-Don", "item_id": "5073"},
    "2001 SCC 44": {"name": "Danyluk", "item_id": "5087"},
    "2011 SCC 52": {"name": "Figliola", "item_id": "8001"},
    "2013 SCC 19": {"name": "Penner", "item_id": "12962"},
    "2002 SCC 79": {"name": "Wewaykum Indian Band", "item_id": "5469"},
    "2003 SCC 63": {"name": "Toronto v. CUPE Local 79", "item_id": "5626"},
    "2004 SCC 5": {"name": "R. v. Lyttle", "item_id": "5707"},
    "2010 SCC 22": {"name": "R. v. Conway", "item_id": "7863"},
    "2015 SCC 5": {"name": "Carter v. Canada", "item_id": "15696"},
}

USER_AGENT = "BC-Legal-AI-Associate/0.1 (lawful public case retrieval; contact: local research tool)"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def identify_court(citation: str) -> str:
    c = (citation or "").upper()
    if "SCC" in c or "SCR" in c:
        return "SCC"
    if "BCCA" in c:
        return "BCCA"
    if "BCSC" in c:
        return "BCSC"
    if "FCA" in c or "CAF" in c:
        return "FCA"
    if "ONCA" in c:
        return "ONCA"
    if "ONSC" in c:
        return "ONSC"
    if "CANLII" in c:
        return "CANLII"
    return "UNKNOWN"


def citation_slug(citation: str) -> str:
    s = re.sub(r"[^\w\s\-]", "", citation)
    s = re.sub(r"\s+", "_", s.strip())
    return s[:80] or "unknown"


def short_name(name: str) -> str:
    s = re.sub(r"[^\w\s\-]", "", name)
    s = re.sub(r"\s+", "_", s.strip())
    return s[:40] or "Case"


def lookup_scc(citation: str) -> Optional[dict[str, str]]:
    raw = (citation or "").strip()
    if raw in SCC_ITEM_IDS:
        return SCC_ITEM_IDS[raw]
    # normalize spaces
    norm = re.sub(r"\s+", " ", raw.upper())
    for k, v in SCC_ITEM_IDS.items():
        if re.sub(r"\s+", " ", k.upper()) == norm:
            return v
    # try match year SCC number
    m = re.search(r"(20\d{2})\s*SCC\s*(\d+)", raw, re.I)
    if m:
        key = f"{m.group(1)} SCC {m.group(2)}"
        if key in SCC_ITEM_IDS:
            return SCC_ITEM_IDS[key]
    return None


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def scc_pdf_url(item_id: str, doc: int = 1) -> str:
    return (
        f"https://decisions.scc-csc.ca/scc-csc/scc-csc/en/{item_id}/{doc}/document.do"
    )


def canlii_search_url(citation: str) -> str:
    q = urllib.parse.quote(citation) if hasattr(urllib, "parse") else citation
    try:
        from urllib.parse import quote

        q = quote(citation)
    except Exception:
        q = citation.replace(" ", "+")
    return f"https://www.canlii.org/en/#search/type=decision&text={q}"


import urllib.parse  # noqa: E402


@dataclass
class DownloadResult:
    tab: int
    citation: str
    case_name: str
    court: str
    status: str
    path: Optional[str] = None
    url: Optional[str] = None
    bytes_size: int = 0
    sha256: Optional[str] = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _http_get(url: str, timeout: int = 60) -> tuple[int, bytes, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/pdf,*/*",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            ctype = resp.headers.get("Content-Type", "")
            return resp.status, data, ctype
    except urllib.error.HTTPError as e:
        return e.code, e.read() if e.fp else b"", ""
    except Exception as e:
        return 0, str(e).encode("utf-8"), "error"


def _is_pdf(data: bytes, ctype: str) -> bool:
    if data[:4] == b"%PDF":
        return True
    if "pdf" in (ctype or "").lower() and data[:4] == b"%PDF":
        return True
    return data[:4] == b"%PDF"


def write_reference_pdf(
    path: Path,
    *,
    citation: str,
    case_name: str,
    court: str,
    url: str,
    reason: str,
) -> int:
    """Minimal valid-ish text file labeled .pdf when blocked — or plain text ref."""
    # Prefer .txt companion if we cannot write real PDF without deps
    body = f"""%PDF-1.1
% Reference document — not the official judgment
1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj
2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj
3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
/Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj
4 0 obj<< /Length 200 >>stream
BT /F1 12 Tf 50 700 Td ({case_name[:40]}) Tj 0 -20 Td ({citation[:40]}) Tj 0 -20 Td (URL: see manifest) Tj ET
endstream endobj
5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000516 00000 n 
trailer<< /Size 6 /Root 1 0 R >>
startxref
593
%%EOF
"""
    # Simpler: write a clear text reference next to a stub
    ref_txt = path.with_suffix(".REFERENCE.txt")
    text = (
        f"REFERENCE ONLY — official PDF not retrieved automatically\n"
        f"Case: {case_name}\n"
        f"Citation: {citation}\n"
        f"Court: {court}\n"
        f"Reason: {reason}\n"
        f"Manual download URL: {url}\n"
        f"Generated: {_utcnow()}\n"
        f"Do not treat this file as the judgment.\n"
    )
    ref_txt.write_text(text, encoding="utf-8")
    # also write minimal pdf-like file for naming consistency
    path.write_bytes(body.encode("latin-1", errors="replace"))
    return path.stat().st_size


def download_case(
    citation: str,
    *,
    output_dir: Path,
    tab: int = 1,
    case_name: Optional[str] = None,
    canlii_url: Optional[str] = None,
) -> DownloadResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    court = identify_court(citation)
    scc = lookup_scc(citation)
    name = case_name or (scc["name"] if scc else "Unknown")
    fname = f"Tab_{tab:02d}_{short_name(name)}_{citation_slug(citation)}.pdf"
    dest = output_dir / fname

    # already exists
    if dest.exists() and dest.stat().st_size > 1000 and dest.read_bytes()[:4] == b"%PDF":
        data = dest.read_bytes()
        if b"Reference document" not in data[:500]:
            return DownloadResult(
                tab=tab,
                citation=citation,
                case_name=name,
                court=court,
                status="ALREADY_EXISTS",
                path=str(dest),
                bytes_size=len(data),
                sha256=sha256_bytes(data),
                message="Valid file present",
            )

    if court == "SCC" and scc:
        item_id = scc["item_id"]
        last_code = 0
        for doc in (1, 2, 3):
            url = scc_pdf_url(item_id, doc)
            code, data, ctype = _http_get(url)
            last_code = code
            if code == 200 and _is_pdf(data, ctype):
                dest.write_bytes(data)
                return DownloadResult(
                    tab=tab,
                    citation=citation,
                    case_name=name,
                    court=court,
                    status="SUCCESS",
                    path=str(dest),
                    url=url,
                    bytes_size=len(data),
                    sha256=sha256_bytes(data),
                    message=f"Downloaded SCC item {item_id} doc={doc}",
                )
            if code in (400, 404):
                continue
            if code == 403:
                break
        url = scc_pdf_url(item_id, 1)
        write_reference_pdf(
            dest,
            citation=citation,
            case_name=name,
            court=court,
            url=url,
            reason=f"SCC fetch failed (last HTTP {last_code})",
        )
        return DownloadResult(
            tab=tab,
            citation=citation,
            case_name=name,
            court=court,
            status="REFERENCE_PDF",
            path=str(dest),
            url=url,
            bytes_size=dest.stat().st_size,
            message=f"HTTP {last_code} — use official URL",
        )

    # CanLII / BC / unknown — no automated CanLII fetch
    url = canlii_url or canlii_search_url(citation)
    reason = (
        "CanLII automated access blocked (Cloudflare) — open URL manually"
        if court in ("CANLII", "BCCA", "BCSC", "ONCA", "ONSC", "UNKNOWN")
        else f"No automated adapter for court {court}"
    )
    if court == "SCC" and not scc:
        reason = "SCC item ID not in verified database — resolve ID then retry"
    write_reference_pdf(
        dest, citation=citation, case_name=name, court=court, url=url, reason=reason
    )
    status = "BLOCKED_CLOUDFLARE" if "Cloudflare" in reason else "REFERENCE_PDF"
    return DownloadResult(
        tab=tab,
        citation=citation,
        case_name=name,
        court=court,
        status=status,
        path=str(dest),
        url=url,
        bytes_size=dest.stat().st_size,
        message=reason,
    )


def download_batch(
    cases: list[dict[str, Any]],
    output_dir: Path,
    *,
    audit_path: Optional[Path] = None,
) -> list[DownloadResult]:
    """
    cases: list of {citation, name?, tab?, canlii_url?}
    """
    results: list[DownloadResult] = []
    cases_dir = output_dir / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)
    audit_path = audit_path or (output_dir / "audit.log")

    for i, c in enumerate(cases, 1):
        tab = int(c.get("tab") or i)
        res = download_case(
            str(c["citation"]),
            output_dir=cases_dir,
            tab=tab,
            case_name=c.get("name"),
            canlii_url=c.get("canlii_url"),
        )
        results.append(res)
        line = (
            f"{_utcnow()} | COURT_DOWNLOAD | {res.case_name} | {res.citation} | "
            f"{res.status} | {res.bytes_size} bytes | "
            f"sha256:{(res.sha256 or '')[:16]}... | {res.url or ''}\n"
        )
        with audit_path.open("a", encoding="utf-8") as f:
            f.write(line)

    _write_reports(output_dir, results)
    return results


def _write_reports(output_dir: Path, results: list[DownloadResult]) -> None:
    manifest = {
        "generated_at": _utcnow(),
        "results": [r.to_dict() for r in results],
        "counts": _counts(results),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    csv_path = output_dir / "table_of_authorities.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Tab", "Case", "Citation", "Court", "Status", "URL", "Path"])
        for r in results:
            w.writerow(
                [r.tab, r.case_name, r.citation, r.court, r.status, r.url or "", r.path or ""]
            )

    counts = _counts(results)
    summary = [
        f"Download summary — {_utcnow()}",
        f"Total: {len(results)}",
        f"SUCCESS: {counts.get('SUCCESS', 0)}",
        f"ALREADY_EXISTS: {counts.get('ALREADY_EXISTS', 0)}",
        f"REFERENCE_PDF: {counts.get('REFERENCE_PDF', 0)}",
        f"BLOCKED_CLOUDFLARE: {counts.get('BLOCKED_CLOUDFLARE', 0)}",
        "",
    ]
    for r in results:
        summary.append(f"  [{r.status}] Tab {r.tab:02d} {r.case_name} — {r.citation}")
    (output_dir / "download_summary.txt").write_text("\n".join(summary), encoding="utf-8")

    missing = [r for r in results if r.status not in ("SUCCESS", "ALREADY_EXISTS")]
    (output_dir / "missing_authorities.txt").write_text(
        "\n".join(f"{r.citation} | {r.status} | {r.url or ''}" for r in missing) or "(none)",
        encoding="utf-8",
    )
    denied = [r for r in results if "BLOCKED" in r.status or r.status == "REFERENCE_PDF"]
    (output_dir / "access_denied.txt").write_text(
        "\n".join(f"{r.citation} | {r.url or ''} | {r.message}" for r in denied) or "(none)",
        encoding="utf-8",
    )


def _counts(results: list[DownloadResult]) -> dict[str, int]:
    c: dict[str, int] = {}
    for r in results:
        c[r.status] = c.get(r.status, 0) + 1
    return c


if __name__ == "__main__":
    import sys

    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("outputs")
    cases = [{"citation": "2019 SCC 65", "name": "Vavilov", "tab": 1}]
    if len(sys.argv) > 2:
        cases = [{"citation": sys.argv[2], "tab": 1}]
    for r in download_batch(cases, out):
        print(r.status, r.path, r.bytes_size)
