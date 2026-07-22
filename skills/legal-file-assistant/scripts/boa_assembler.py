"""
Lightweight BOA assembler — concatenates available PDFs with a text TOC.

Full court-ready BOA still requires human counsel review and official PDFs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def assemble_boa(
    case_pdfs: list[Path],
    output_path: Path,
    *,
    title: str = "Book of Authorities (Working Draft)",
) -> Path:
    """
    If pypdf available, merge PDFs. Else write a TOC text package.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    existing = [p for p in case_pdfs if p.is_file()]

    try:
        from pypdf import PdfReader, PdfWriter  # type: ignore

        writer = PdfWriter()
        # No real cover page PDF — merge bodies only
        for p in existing:
            try:
                if p.read_bytes()[:4] != b"%PDF":
                    continue
                if b"Reference document" in p.read_bytes()[:800]:
                    continue  # skip stub refs from merge of "official" BOA
                reader = PdfReader(str(p))
                for page in reader.pages:
                    writer.add_page(page)
            except Exception:
                continue
        if len(writer.pages) == 0:
            raise RuntimeError("no mergeable pages")
        with output_path.open("wb") as f:
            writer.write(f)
        return output_path
    except Exception:
        toc = [
            title,
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            "STATUS: Working draft — not court-ready. Verify each authority on official source.",
            "",
            "Table of contents / file list:",
        ]
        for i, p in enumerate(existing, 1):
            toc.append(f"  Tab {i:02d}: {p.name}  →  {p}")
        toc.append("")
        toc.append("Official PDFs not fully merged (install pypdf for merge).")
        alt = output_path.with_suffix(".toc.txt")
        alt.write_text("\n".join(toc), encoding="utf-8")
        return alt


def build_from_manifest(manifest: dict[str, Any], output_dir: Path) -> Optional[Path]:
    paths = []
    for r in manifest.get("results") or []:
        p = r.get("path")
        if p and Path(p).is_file() and r.get("status") in ("SUCCESS", "ALREADY_EXISTS"):
            paths.append(Path(p))
    if not paths:
        return None
    return assemble_boa(paths, output_dir / "BOA_working_draft.pdf")
