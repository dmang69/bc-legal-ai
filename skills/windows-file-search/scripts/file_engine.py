"""
Windows desktop file and folder search.

Safety: never System32/SysWOW64/WinSxS/credential stores.
No permission bypass. No remote access unless user roots say so.
Minimize content logging — snippets only on content hits.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Safety
# ---------------------------------------------------------------------------

PROTECTED_FRAGMENTS = (
    "\\windows\\system32",
    "\\windows\\syswow64",
    "\\windows\\winsxs",
    "\\windows\\system32\\config",
    "\\appdata\\local\\microsoft\\credentials",
    "\\appdata\\roaming\\microsoft\\credentials",
    "\\appdata\\local\\microsoft\\vault",
    "/windows/system32",
    "/windows/syswow64",
)

DEFAULT_EXCLUDE = [
    r"C:\Windows",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    r"C:\ProgramData",
    r"$Recycle.Bin",
]


def is_protected(path: str) -> bool:
    low = path.lower().replace("/", "\\")
    if any(p in low for p in PROTECTED_FRAGMENTS):
        return True
    # SAM/SECURITY/SYSTEM hive names
    name = Path(path).name.lower()
    if name in ("sam", "security", "system", "ntds.dit"):
        return True
    return False


def default_roots() -> list[str]:
    home = Path.home()
    roots = [
        str(home / "Documents"),
        str(home / "Downloads"),
        str(home / "Desktop"),
    ]
    for name in ("OneDrive", "OneDrive - Personal"):
        p = home / name
        if p.is_dir():
            roots.append(str(p))
            break
    # legal project outputs if present
    for extra in (
        home / "projects" / "bc-legal-ai",
        Path(__file__).resolve().parents[3] / "skills" / "canadian-court-downloader" / "outputs",
        Path(__file__).resolve().parents[3] / "skills" / "legal-file-assistant" / "outputs",
    ):
        try:
            if extra.is_dir():
                roots.append(str(extra))
        except OSError:
            pass
    return [r for r in roots if Path(r).is_dir() and not is_protected(r)]


# ---------------------------------------------------------------------------
# Params / results
# ---------------------------------------------------------------------------


@dataclass
class SearchParams:
    query_text: str = ""
    file_name: str = ""
    folder_name: str = ""
    extension: list[str] = field(default_factory=list)
    root_paths: list[str] = field(default_factory=list)
    exclude_paths: list[str] = field(default_factory=list)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    size_min_kb: Optional[int] = None
    size_max_kb: Optional[int] = None
    content_keywords: list[str] = field(default_factory=list)
    include_hidden: bool = False
    include_system: bool = False
    search_type: str = "files"  # files | folders | both
    sort_by: str = "relevance"  # name | date | size | relevance
    max_results: int = 50
    fuzzy: bool = True
    find_duplicates: bool = False
    export_format: Optional[str] = None
    use_powershell: bool = True
    use_windows_index: bool = False


@dataclass
class FileResult:
    result_type: str
    name: str
    path: str
    parent_folder: str
    extension: str = ""
    size_bytes: int = 0
    size_human: str = ""
    created_at: str = ""
    modified_at: str = ""
    match_type: str = ""
    relevance_score: float = 0.0
    match_explanation: str = ""
    content_snippet: Optional[str] = None
    file_count: Optional[int] = None  # folders

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if d.get("file_count") is None:
            d.pop("file_count", None)
        return d


@dataclass
class SearchStats:
    files_scanned: int = 0
    folders_scanned: int = 0
    permission_skipped: int = 0
    protected_skipped: int = 0
    method: str = "os.walk"


def human_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024**2:
        return f"{n / 1024:.0f} KB"
    if n < 1024**3:
        return f"{n / (1024**2):.1f} MB"
    return f"{n / (1024**3):.2f} GB"


# ---------------------------------------------------------------------------
# NL parse
# ---------------------------------------------------------------------------


def parse_nl(query: str) -> SearchParams:
    q = query or ""
    low = q.lower()
    p = SearchParams(query_text=q)

    if "duplicate" in low:
        p.find_duplicates = True
    if re.search(r"\bfolders?\b", low) and "file" not in low:
        p.search_type = "folders"
    elif "folder" in low and "file" in low:
        p.search_type = "both"

    if "last week" in low:
        p.date_from = datetime.now() - timedelta(days=7)
        p.sort_by = "date"
    if "last month" in low:
        p.date_from = datetime.now() - timedelta(days=30)
        p.sort_by = "date"
    if "latest" in low or "most recent" in low:
        p.sort_by = "date"

    if "pdf" in low:
        p.extension.append(".pdf")
    if "docx" in low or "word" in low:
        p.extension.append(".docx")
    if "txt" in low:
        p.extension.append(".txt")
    p.extension = list(dict.fromkeys(p.extension))

    if any(w in low for w in ("court", "judgment", "tenancy", "rtb", "boa", "authority")):
        if not p.extension:
            p.extension = [".pdf", ".docx", ".txt"]

    # content search phrase
    m = re.search(r"(?:inside|within|containing|content|for)\s+[\"']?([\w\-\.]+)[\"']?", low)
    if "search inside" in low or "inside my" in low or "content" in low:
        # take last meaningful token
        tokens = re.findall(r"[a-z0-9\-]{2,}", low)
        skip = {
            "search", "inside", "my", "documents", "for", "find", "the", "files",
            "file", "all", "pdf", "docx", "folder", "folders", "containing",
        }
        content = [t for t in tokens if t not in skip]
        if content:
            p.content_keywords = [content[-1]]

    # root hints
    home = Path.home()
    if "download" in low:
        p.root_paths = [str(home / "Downloads")]
    elif "desktop" in low:
        p.root_paths = [str(home / "Desktop")]
    elif "document" in low and "inside" not in low:
        # "search my documents" as root
        if "search inside" not in low:
            p.root_paths = p.root_paths or [str(home / "Documents")]

    # clean query for filename
    cleaned = re.sub(
        r"\b(find|my|the|file|files|search|for|where|is|locate|all|pdf|docx|"
        r"document|documents|folder|folders|anything|modified|last|week|month|"
        r"duplicates?|in|downloads?|desktop|latest|version|of|show|me|"
        r"containing|related|to|everything|export|list|csv|json|"
        r"inside|content|keyword)\b",
        " ",
        low,
        flags=re.I,
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if cleaned:
        p.file_name = cleaned
        p.query_text = cleaned
        if p.search_type == "folders":
            p.folder_name = cleaned

    if "export" in low and "csv" in low:
        p.export_format = "csv"
    elif "export" in low and "json" in low:
        p.export_format = "json"

    return p


# ---------------------------------------------------------------------------
# Matching / scoring
# ---------------------------------------------------------------------------


def _fuzzy_match(query: str, target: str, threshold: float = 0.7) -> bool:
    """
    Token/substring fuzzy only — NOT character-bag overlap (that matched almost everything).
    """
    if not query:
        return True
    if query in target:
        return True
    q_tokens = [t for t in re.split(r"\W+", query) if len(t) >= 3]
    if not q_tokens:
        return query in target
    # require majority of tokens as substrings
    hits = sum(1 for t in q_tokens if t in target)
    return (hits / len(q_tokens)) >= threshold


def score_result(
    path: Path,
    *,
    query: str,
    match_type: str,
    content_hit: bool,
    is_folder: bool = False,
) -> tuple[float, str]:
    name = path.name.lower()
    q = (query or "").lower()
    score = 0.0
    expl: list[str] = []

    if is_folder:
        if q and q == name:
            score = 1.0
            expl.append("Exact folder name match")
        elif q and q in name:
            score = 0.6
            expl.append("Folder name contains search term")
        else:
            score = 0.4
    else:
        if q and q == name:
            score = 1.0
            expl.append("Exact filename match")
            match_type = "filename_exact"
        elif q and q in name:
            score = max(0.7 * min(1.0, len(q) / max(len(name), 1)), 0.55)
            expl.append(f"Query '{q}' found in filename")
            match_type = "filename_partial"
        elif q:
            tokens = [t for t in re.split(r"\W+", q) if t]
            hits = sum(1 for t in tokens if t in name)
            if hits:
                score = 0.4 * (hits / len(tokens))
                expl.append("Partial token match in filename")
                match_type = "filename_token"
        if content_hit:
            score = max(score, 0.5)
            score += 0.15
            expl.append("Content keyword match")

    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        age = (datetime.now() - mtime).days
        if age < 7:
            score += 0.2
        elif age < 30:
            score += 0.1
    except OSError:
        pass

    try:
        home = str(Path.home()).lower()
        if str(path).lower().startswith(home):
            score += 0.1
    except Exception:
        pass

    if not is_folder and path.suffix.lower() in (".pdf", ".docx"):
        score += 0.05

    return min(score, 1.0), "; ".join(expl) or match_type


# ---------------------------------------------------------------------------
# Content search
# ---------------------------------------------------------------------------


def _find_snippet(text: str, keywords: list[str], context_chars: int = 150) -> Optional[str]:
    low = text.lower()
    for kw in keywords:
        i = low.find(kw.lower())
        if i >= 0:
            start = max(0, i - context_chars // 2)
            end = min(len(text), i + len(kw) + context_chars // 2)
            return text[start:end].replace("\n", " ").strip()
    return None


def search_content(filepath: Path, keywords: list[str]) -> dict[str, Any]:
    ext = filepath.suffix.lower()
    try:
        if not os.access(filepath, os.R_OK):
            return {"found": False, "status": "permission_denied"}
        if ext in (".txt", ".py", ".js", ".html", ".css", ".md", ".csv", ".json", ".log", ".htm"):
            text = filepath.read_text(encoding="utf-8", errors="ignore")[:100_000]
            snip = _find_snippet(text, keywords)
            return {"found": bool(snip), "snippet": snip, "status": "ok"}
        if ext == ".pdf":
            try:
                from pypdf import PdfReader  # type: ignore

                reader = PdfReader(str(filepath))
                for i, page in enumerate(reader.pages[:10]):
                    text = page.extract_text() or ""
                    snip = _find_snippet(text, keywords)
                    if snip:
                        return {"found": True, "snippet": snip, "page": i + 1, "status": "ok"}
                return {
                    "found": False,
                    "status": "no_text_in_pdf",
                    "note": "PDF may be scanned. Install pytesseract for OCR.",
                }
            except Exception as e:
                return {"found": False, "status": "error", "note": str(e)}
        if ext == ".docx":
            import zipfile

            with zipfile.ZipFile(filepath) as z:
                xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
            text = re.sub(r"<[^>]+>", " ", xml)[:100_000]
            snip = _find_snippet(text, keywords)
            return {"found": bool(snip), "snippet": snip, "status": "ok"}
        return {"found": False, "status": "unsupported", "note": f"No content search for {ext}"}
    except PermissionError:
        return {"found": False, "status": "permission_denied"}
    except Exception as e:
        return {"found": False, "status": "error", "note": str(e)}


# ---------------------------------------------------------------------------
# Engines
# ---------------------------------------------------------------------------


def search_powershell(
    query: str,
    root_path: str,
    extension: str = "",
    max_results: int = 50,
) -> list[dict[str, Any]]:
    if is_protected(root_path):
        return []
    filt = f"*{query}*{extension}" if extension else f"*{query}*"
    # Escape for PowerShell single-quoted path
    root_ps = root_path.replace("'", "''")
    filt_ps = filt.replace("'", "''")
    ps_cmd = f"""
$ErrorActionPreference = 'SilentlyContinue'
Get-ChildItem -LiteralPath '{root_ps}' -Recurse -File -Filter '{filt_ps}' |
  Select-Object -First {int(max_results)} FullName, Name, Length, LastWriteTime, CreationTime, Extension |
  ConvertTo-Json -Compress
"""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=90,
        )
        if not result.stdout.strip():
            return []
        items = json.loads(result.stdout)
        if isinstance(items, dict):
            items = [items]
        return items
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return []


def search_os_walk(params: SearchParams) -> tuple[list[FileResult], SearchStats]:
    stats = SearchStats(method="os.walk")
    roots = params.root_paths or default_roots()
    excludes = list(params.exclude_paths or []) + DEFAULT_EXCLUDE
    query = (params.file_name or params.query_text or params.folder_name or "").strip()
    exts = [
        e.lower() if e.startswith(".") else f".{e.lower()}" for e in params.extension
    ]
    results: list[FileResult] = []

    for root in roots:
        root_p = Path(root)
        if not root_p.is_dir() or is_protected(root):
            stats.protected_skipped += 1
            continue
        try:
            for dirpath, dirnames, filenames in os.walk(root):
                if is_protected(dirpath):
                    stats.protected_skipped += 1
                    dirnames.clear()
                    continue
                if any(ex.lower() in dirpath.lower() for ex in excludes if ex):
                    dirnames.clear()
                    continue

                if not params.include_hidden:
                    dirnames[:] = [
                        d
                        for d in dirnames
                        if not d.startswith(".") and not d.startswith("$")
                    ]

                stats.folders_scanned += 1

                if params.search_type in ("folders", "both"):
                    for d in list(dirnames):
                        if query:
                            dl = d.lower()
                            ql = query.lower()
                            ok = ql in dl or (params.fuzzy and _fuzzy_match(ql, dl))
                            if not ok:
                                continue
                        fp = Path(dirpath) / d
                        if is_protected(str(fp)):
                            continue
                        score, expl = score_result(
                            fp, query=query, match_type="folder_name_partial", content_hit=False, is_folder=True
                        )
                        try:
                            nfiles = sum(1 for _ in fp.iterdir() if _.is_file())
                        except (OSError, PermissionError):
                            nfiles = 0
                            stats.permission_skipped += 1
                        results.append(
                            FileResult(
                                result_type="folder",
                                name=d,
                                path=str(fp),
                                parent_folder=str(fp.parent),
                                match_type="folder_name_partial",
                                relevance_score=score,
                                match_explanation=expl,
                                file_count=nfiles,
                            )
                        )
                        if len(results) >= params.max_results:
                            return _sort(results, params)[: params.max_results], stats

                if params.search_type in ("files", "both"):
                    for fn in filenames:
                        stats.files_scanned += 1
                        if not params.include_hidden and (
                            fn.startswith(".") or fn.startswith("~$")
                        ):
                            continue
                        fp = Path(dirpath) / fn
                        if is_protected(str(fp)):
                            stats.protected_skipped += 1
                            continue
                        if not params.include_system:
                            # skip common junk
                            if fn.lower() in ("thumbs.db", "desktop.ini"):
                                continue
                        if exts and fp.suffix.lower() not in exts:
                            continue
                        try:
                            if not os.access(fp, os.R_OK):
                                stats.permission_skipped += 1
                                continue
                            st = fp.stat()
                        except (OSError, PermissionError):
                            stats.permission_skipped += 1
                            continue

                        mtime = datetime.fromtimestamp(st.st_mtime)
                        if params.date_from and mtime < params.date_from:
                            continue
                        if params.date_to and mtime > params.date_to:
                            continue
                        size_kb = st.st_size / 1024
                        if params.size_min_kb is not None and size_kb < params.size_min_kb:
                            continue
                        if params.size_max_kb is not None and size_kb > params.size_max_kb:
                            continue

                        name_match = True
                        if query:
                            fl = fn.lower()
                            ql = query.lower()
                            name_match = ql in fl
                            if not name_match and params.fuzzy:
                                # multi-word: each significant token; single word: substring only
                                tokens = [t for t in re.split(r"\W+", ql) if len(t) >= 3]
                                if len(tokens) >= 2:
                                    name_match = _fuzzy_match(ql, fl)
                                else:
                                    # single token — require contiguous substring (no char soup)
                                    name_match = bool(tokens) and tokens[0] in fl

                        content_hit = False
                        snippet = None
                        if params.content_keywords:
                            cre = search_content(fp, params.content_keywords)
                            content_hit = bool(cre.get("found"))
                            snippet = cre.get("snippet")
                            if not content_hit and not name_match:
                                continue
                        elif not name_match:
                            continue

                        score, expl = score_result(
                            fp,
                            query=query,
                            match_type="filename",
                            content_hit=content_hit,
                        )
                        try:
                            ctime = datetime.fromtimestamp(st.st_ctime).isoformat(timespec="seconds")
                        except Exception:
                            ctime = ""
                        results.append(
                            FileResult(
                                result_type="file",
                                name=fn,
                                path=str(fp),
                                parent_folder=str(fp.parent),
                                extension=fp.suffix.lower(),
                                size_bytes=st.st_size,
                                size_human=human_size(st.st_size),
                                created_at=ctime,
                                modified_at=mtime.isoformat(timespec="seconds"),
                                match_type="content"
                                if content_hit and not name_match
                                else "filename_partial",
                                relevance_score=score,
                                match_explanation=expl,
                                content_snippet=snippet,
                            )
                        )
                        if len(results) >= params.max_results * 3:
                            # early stop gathering, still sort/cap later
                            break
        except (OSError, PermissionError):
            stats.permission_skipped += 1
            continue

    return _sort(results, params)[: params.max_results], stats


def search_with_powershell_boost(params: SearchParams) -> tuple[list[FileResult], SearchStats]:
    """Prefer PowerShell filter on each root when query is simple; merge with walk scores."""
    query = (params.file_name or params.query_text or "").strip()
    if not query or params.find_duplicates or params.content_keywords or params.search_type == "folders":
        return search_os_walk(params)

    roots = params.root_paths or default_roots()
    ext = ""
    if len(params.extension) == 1:
        ext = params.extension[0]
    results: list[FileResult] = []
    stats = SearchStats(method="powershell+os.walk")
    seen: set[str] = set()

    for root in roots:
        if is_protected(root):
            continue
        items = search_powershell(query, root, extension=ext, max_results=params.max_results)
        for it in items:
            path = it.get("FullName") or ""
            if not path or path in seen or is_protected(path):
                continue
            seen.add(path)
            fp = Path(path)
            try:
                size = int(it.get("Length") or 0)
                # PowerShell dates may be /Date(ms)/
                mraw = str(it.get("LastWriteTime") or "")
                craw = str(it.get("CreationTime") or "")
            except Exception:
                size = 0
                mraw = craw = ""
            score, expl = score_result(
                fp, query=query, match_type="filename_partial", content_hit=False
            )
            results.append(
                FileResult(
                    result_type="file",
                    name=it.get("Name") or fp.name,
                    path=path,
                    parent_folder=str(fp.parent),
                    extension=(it.get("Extension") or fp.suffix).lower(),
                    size_bytes=size,
                    size_human=human_size(size),
                    created_at=craw,
                    modified_at=mraw,
                    match_type="filename_partial",
                    relevance_score=score,
                    match_explanation=expl + " (PowerShell)",
                )
            )
            stats.files_scanned += 1

    if len(results) < 5:
        # fill with walk
        more, st2 = search_os_walk(params)
        stats.files_scanned += st2.files_scanned
        stats.permission_skipped += st2.permission_skipped
        for r in more:
            if r.path not in seen:
                results.append(r)

    return _sort(results, params)[: params.max_results], stats


def search(params: SearchParams) -> tuple[list[FileResult], SearchStats]:
    if params.find_duplicates:
        return find_duplicates(params)

    if params.use_powershell and os.name == "nt":
        return search_with_powershell_boost(params)
    return search_os_walk(params)


def _sort(results: list[FileResult], params: SearchParams) -> list[FileResult]:
    if params.sort_by in ("date", "date_desc"):
        return sorted(results, key=lambda r: r.modified_at or "", reverse=True)
    if params.sort_by == "size":
        return sorted(results, key=lambda r: r.size_bytes, reverse=True)
    if params.sort_by == "name":
        return sorted(results, key=lambda r: r.name.lower())
    return sorted(results, key=lambda r: r.relevance_score, reverse=True)


def find_duplicates(params: SearchParams) -> tuple[list[FileResult], SearchStats]:
    stats = SearchStats(method="sha256_duplicates")
    roots = params.root_paths or default_roots()
    exts = [
        e.lower() if e.startswith(".") else f".{e.lower()}" for e in params.extension
    ] or [".pdf", ".docx", ".txt"]
    hashes: dict[str, list[Path]] = {}

    for root in roots:
        if is_protected(root) or not Path(root).is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            if is_protected(dirpath):
                dirnames.clear()
                stats.protected_skipped += 1
                continue
            for fn in filenames:
                fp = Path(dirpath) / fn
                if exts and fp.suffix.lower() not in exts:
                    continue
                try:
                    if not os.access(fp, os.R_OK):
                        stats.permission_skipped += 1
                        continue
                    st = fp.stat()
                    if st.st_size > 80 * 1024 * 1024:
                        continue
                    stats.files_scanned += 1
                    h = _sha256_file(fp)
                    hashes.setdefault(h, []).append(fp)
                except (OSError, PermissionError):
                    stats.permission_skipped += 1

    out: list[FileResult] = []
    for h, paths in hashes.items():
        if len(paths) < 2:
            continue
        original = max(paths, key=lambda p: p.stat().st_size)
        for p in paths:
            if p == original:
                continue
            st = p.stat()
            out.append(
                FileResult(
                    result_type="duplicate",
                    name=p.name,
                    path=str(p),
                    parent_folder=str(p.parent),
                    extension=p.suffix.lower(),
                    size_bytes=st.st_size,
                    size_human=human_size(st.st_size),
                    modified_at=datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
                    match_type="sha256_duplicate",
                    relevance_score=1.0,
                    match_explanation=f"Duplicate of {original} (sha256:{h[:16]}…)",
                    content_snippet=str(original),
                )
            )
    return out[: params.max_results], stats


def _sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def export_results(
    results: list[FileResult],
    output_path: Path,
    fmt: str = "csv",
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [r.to_dict() for r in results]
    if fmt == "json":
        output_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    elif fmt == "txt":
        lines = [
            f"{r.path} | {r.size_human} | {r.modified_at} | {r.relevance_score:.2f}"
            for r in results
        ]
        output_path.write_text("\n".join(lines), encoding="utf-8")
    else:
        with output_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=[
                    "name",
                    "path",
                    "extension",
                    "size_bytes",
                    "modified_at",
                    "match_type",
                    "relevance_score",
                ],
            )
            w.writeheader()
            for r in results:
                w.writerow(
                    {
                        "name": r.name,
                        "path": r.path,
                        "extension": r.extension,
                        "size_bytes": r.size_bytes,
                        "modified_at": r.modified_at,
                        "match_type": r.match_type,
                        "relevance_score": f"{r.relevance_score:.2f}",
                    }
                )
    return output_path


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) or "vavilov"
    params = parse_nl(q)
    if not params.extension and "vavilov" in q.lower():
        params.extension = [".pdf"]
    res, st = search(params)
    print(f"method={st.method} scanned={st.files_scanned} skipped_perm={st.permission_skipped}")
    for r in res[:20]:
        print(f"{r.relevance_score:.2f}\t{r.path}")
