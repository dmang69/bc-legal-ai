"""Copilot-style code assistance — structured, multi-language, fail-closed.

Does not execute untrusted code. Provides completion scaffolds, debug checklists,
and documentation drafts. Optional LLM enhancement via model providers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


LANG_HINTS = {
    "python": ["def ", "import ", "class ", "pytest"],
    "typescript": ["const ", "interface ", "export ", "async "],
    "javascript": ["function ", "const ", "=>"],
    "rust": ["fn ", "impl ", "let mut"],
    "go": ["func ", "package ", "err !="],
    "sql": ["SELECT ", "INSERT ", "CREATE TABLE"],
}


@dataclass
class CodeAssistResult:
    ok: bool
    mode: str
    language: str
    content: str
    suggestions: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "mode": self.mode,
            "language": self.language,
            "content": self.content,
            "suggestions": self.suggestions,
            "meta": self.meta,
            "executes_code": False,
        }


def detect_language(code: str, explicit: str = "") -> str:
    if explicit:
        return explicit.lower()
    scores = {lang: sum(1 for h in hints if h in (code or "")) for lang, hints in LANG_HINTS.items()}
    best = max(scores, key=scores.get) if scores else "text"
    return best if scores.get(best, 0) > 0 else "text"


def complete_code(code: str, *, language: str = "", intent: str = "continue") -> CodeAssistResult:
    lang = detect_language(code, language)
    suggestions = [
        f"Keep {lang} style consistent with surrounding project conventions.",
        "Add type hints / interfaces where public APIs are involved.",
        "Handle errors explicitly; avoid bare excepts.",
        "Write a unit test for the happy path and one failure path.",
    ]
    body = (
        f"**Code assist ({intent}) — {lang}**\n\n"
        "```" + lang + "\n"
        f"{(code or '').rstrip()}\n"
        "# TODO: complete implementation; do not invent secret keys or live credentials\n"
        "```\n\n"
        "**Suggestions**\n"
        + "\n".join(f"- {s}" for s in suggestions)
        + "\n\n_Does not execute code. Review before merge._"
    )
    return CodeAssistResult(True, "complete", lang, body, suggestions)


def debug_code(code: str, error: str = "", *, language: str = "") -> CodeAssistResult:
    lang = detect_language(code, language)
    steps = [
        "Reproduce with a minimal failing case.",
        "Read the full stack trace / type error carefully.",
        "Check recent changes (git blame / diff).",
        "Validate inputs and null/None boundaries.",
        "Add logging at the failure boundary, then remove noise.",
        "Add a regression test once fixed.",
    ]
    body = (
        f"**Debug checklist — {lang}**\n\n"
        f"**Error report:** {error or '[paste error]'}\n\n"
        + "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))
        + "\n\n**Snippet under review**\n```"
        + lang
        + f"\n{(code or '')[:4000]}\n```"
    )
    return CodeAssistResult(True, "debug", lang, body, steps, meta={"error": error})


def document_code(code: str, *, language: str = "", style: str = "docstring") -> CodeAssistResult:
    lang = detect_language(code, language)
    body = (
        f"**Documentation draft ({style}) — {lang}**\n\n"
        "```" + lang + "\n"
        '"""\n'
        "Summary: [one sentence].\n\n"
        "Args:\n"
        "    [name]: [description]\n\n"
        "Returns:\n"
        "    [description]\n\n"
        "Raises:\n"
        "    [Exception]: when …\n"
        '"""\n'
        f"{(code or '')[:3000]}\n"
        "```\n\n"
        "Document public APIs; keep internal helpers concise."
    )
    return CodeAssistResult(True, "document", lang, body)
