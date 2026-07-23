"""Native PDF text extraction (M2) — optional pypdf; fail closed without dependency."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExtractedPage:
    page_number: int
    text: str
    page_hash: str
    confidence: float = 1.0
    needs_review: bool = False


@dataclass
class ExtractResult:
    ok: bool
    engine: str
    pages: list[ExtractedPage] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "engine": self.engine,
            "page_count": len(self.pages),
            "error": self.error,
            "pages": [
                {
                    "page_number": p.page_number,
                    "chars": len(p.text),
                    "page_hash": p.page_hash,
                    "needs_review": p.needs_review,
                    "confidence": p.confidence,
                }
                for p in self.pages
            ],
        }


def extract_pdf_bytes(data: bytes) -> ExtractResult:
    if not data:
        return ExtractResult(ok=False, engine="none", error="empty")
    # PDF magic
    if not data[:5].startswith(b"%PDF"):
        return ExtractResult(ok=False, engine="none", error="not a PDF")
    try:
        from pypdf import PdfReader  # type: ignore
        import io

        reader = PdfReader(io.BytesIO(data))
        pages: list[ExtractedPage] = []
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            conf = 1.0 if text.strip() else 0.0
            needs = conf < 0.5 or len(text.strip()) < 20
            pages.append(
                ExtractedPage(
                    page_number=i,
                    text=text,
                    page_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    confidence=conf,
                    needs_review=needs,
                )
            )
        return ExtractResult(ok=True, engine="pypdf", pages=pages)
    except ImportError:
        return ExtractResult(
            ok=False,
            engine="unavailable",
            error="pypdf not installed; pip install pypdf",
        )
    except Exception as e:
        return ExtractResult(ok=False, engine="pypdf", error=str(e))
