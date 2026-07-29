"""OCR layer for scanned PDF pages (M2).

Pipeline:
  1. Native text via pypdf (pdf_extract)
  2. For empty/low-text pages, attempt OCR if engine available
  3. Always record confidence + needs_review; never invent text

OCR requires optional deps: pytesseract + pdf2image (+ system Tesseract + Poppler).
Without them, pages are marked NEEDS_OCR rather than fabricated.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from typing import Any

from backend.platform.pdf_extract import ExtractResult, extract_pdf_bytes


@dataclass
class OcrPageResult:
    page_number: int
    text: str
    page_hash: str
    confidence: float
    engine: str
    needs_review: bool
    needs_ocr: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_number": self.page_number,
            "chars": len(self.text),
            "page_hash": self.page_hash,
            "confidence": self.confidence,
            "engine": self.engine,
            "needs_review": self.needs_review,
            "needs_ocr": self.needs_ocr,
        }


@dataclass
class OcrDocumentResult:
    ok: bool
    engine: str
    pages: list[OcrPageResult] = field(default_factory=list)
    error: str = ""
    ocr_attempted: bool = False
    ocr_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "engine": self.engine,
            "page_count": len(self.pages),
            "error": self.error,
            "ocr_attempted": self.ocr_attempted,
            "ocr_available": self.ocr_available,
            "pages": [p.to_dict() for p in self.pages],
        }


def ocr_engine_available() -> bool:
    if os.environ.get("ALA_OCR_DISABLED", "").strip() in ("1", "true", "yes"):
        return False
    try:
        import pytesseract  # noqa: F401
        import pdf2image  # noqa: F401

        return True
    except ImportError:
        return False


def _ocr_page_image(image) -> tuple[str, float]:
    import pytesseract

    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    texts = []
    confs: list[float] = []
    for i, word in enumerate(data.get("text") or []):
        w = (word or "").strip()
        if not w:
            continue
        texts.append(w)
        try:
            c = float(data["conf"][i])
            if c >= 0:
                confs.append(c / 100.0)
        except (ValueError, KeyError, IndexError, TypeError):
            pass
    text = " ".join(texts)
    conf = sum(confs) / len(confs) if confs else (0.5 if text else 0.0)
    return text, conf


def _try_ocr_pdf_pages(data: bytes, page_numbers: list[int]) -> dict[int, tuple[str, float]]:
    """OCR selected 1-based page numbers. Returns map page_number -> (text, conf)."""
    from pdf2image import convert_from_bytes

    images = convert_from_bytes(data, dpi=int(os.environ.get("ALA_OCR_DPI", "200")))
    out: dict[int, tuple[str, float]] = {}
    for n in page_numbers:
        if n < 1 or n > len(images):
            continue
        text, conf = _ocr_page_image(images[n - 1])
        out[n] = (text, conf)
    return out


def extract_with_ocr(
    data: bytes,
    *,
    force_ocr: bool = False,
    min_chars: int = 20,
) -> OcrDocumentResult:
    """Native extract first; OCR empty/low pages when engine available."""
    base: ExtractResult = extract_pdf_bytes(data)
    if not base.ok and base.engine == "none":
        return OcrDocumentResult(ok=False, engine=base.engine, error=base.error)
    if not base.ok and not base.pages:
        return OcrDocumentResult(ok=False, engine=base.engine, error=base.error)

    available = ocr_engine_available()
    pages_out: list[OcrPageResult] = []
    need_ocr_nums: list[int] = []

    for p in base.pages:
        low = force_ocr or p.needs_review or len((p.text or "").strip()) < min_chars
        if low:
            need_ocr_nums.append(p.page_number)
        pages_out.append(
            OcrPageResult(
                page_number=p.page_number,
                text=p.text,
                page_hash=p.page_hash,
                confidence=p.confidence,
                engine=base.engine or "pypdf",
                needs_review=p.needs_review,
                needs_ocr=low,
            )
        )

    ocr_attempted = False
    if need_ocr_nums and available:
        ocr_attempted = True
        try:
            ocr_map = _try_ocr_pdf_pages(data, need_ocr_nums)
            rebuilt: list[OcrPageResult] = []
            for p in pages_out:
                if p.page_number in ocr_map:
                    text, conf = ocr_map[p.page_number]
                    # Prefer OCR when native was empty; else keep richer native
                    if len(text.strip()) > len((p.text or "").strip()):
                        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
                        rebuilt.append(
                            OcrPageResult(
                                page_number=p.page_number,
                                text=text,
                                page_hash=h,
                                confidence=conf,
                                engine="tesseract",
                                needs_review=conf < 0.7 or len(text.strip()) < min_chars,
                                needs_ocr=False,
                            )
                        )
                        continue
                rebuilt.append(p)
            pages_out = rebuilt
        except Exception as e:
            return OcrDocumentResult(
                ok=bool(pages_out),
                engine="ocr_error",
                pages=pages_out,
                error=str(e),
                ocr_attempted=True,
                ocr_available=available,
            )

    return OcrDocumentResult(
        ok=True,
        engine="pypdf+ocr" if ocr_attempted else (base.engine or "pypdf"),
        pages=pages_out,
        ocr_attempted=ocr_attempted,
        ocr_available=available,
    )
