"""Monica-inspired productivity tools — deterministic + optional LLM enhancement.

All tools are fail-closed: no silent external egress; legal outputs never court_ready.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolResult:
    ok: bool
    tool: str
    title: str
    content: str
    court_ready: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "tool": self.tool,
            "title": self.title,
            "content": self.content,
            "court_ready": self.court_ready,
            "meta": self.meta,
        }


def summarize_text(text: str, *, max_bullets: int = 8) -> ToolResult:
    text = (text or "").strip()
    if not text:
        return ToolResult(False, "summarize", "Summary", "No text provided.")
    # Prefer paragraph/sentence splits
    chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
    chunks = [c.strip() for c in chunks if len(c.strip()) > 40]
    if not chunks:
        chunks = [text[:280]]
    # Score by length + keyword density (simple)
    keywords = ("must", "shall", "order", "deadline", "because", "however", "therefore")
    scored = sorted(
        chunks,
        key=lambda c: len(c) + 40 * sum(1 for k in keywords if k in c.lower()),
        reverse=True,
    )
    bullets = scored[:max_bullets]
    body = "**Summary (extractive)**\n\n" + "\n".join(f"- {b}" for b in bullets)
    body += (
        f"\n\n_Source length: {len(text)} chars · bullets: {len(bullets)}. "
        "Not legal advice; verify against full record._"
    )
    return ToolResult(
        True,
        "summarize",
        "Document summary",
        body,
        meta={"bullets": len(bullets), "source_chars": len(text)},
    )


def draft_email(
    *,
    purpose: str,
    audience: str = "colleague",
    tone: str = "professional",
    points: Optional[list[str]] = None,
    matter_label: str = "",
) -> ToolResult:
    points = points or []
    subject = purpose.strip()[:80] or "Follow-up"
    if matter_label:
        subject = f"{matter_label}: {subject}"
    bullets = "\n".join(f"- {p}" for p in points) or "- [Key point 1]\n- [Key point 2]"
    body = (
        f"**Subject:** {subject}\n\n"
        f"Dear {audience},\n\n"
        f"I am writing regarding {purpose.strip() or '[topic]'}.\n\n"
        f"{bullets}\n\n"
        "Please let me know if you need anything further.\n\n"
        "Kind regards,\n"
        "[Your name]\n\n"
        f"_Tone: {tone}. Draft only — review before send. Not legal advice._"
    )
    return ToolResult(True, "email_draft", "Email draft", body, meta={"tone": tone})


def creative_writing(prompt: str, *, style: str = "clear_prose") -> ToolResult:
    prompt = (prompt or "").strip()
    if not prompt:
        return ToolResult(False, "creative", "Creative writing", "No prompt provided.")
    # Structured scaffold — optional LLM can expand via provider
    body = (
        f"**Creative draft ({style})**\n\n"
        f"**Prompt:** {prompt}\n\n"
        "**Opening**\n"
        f"{prompt[:200]}…\n\n"
        "**Development**\n"
        "- Establish setting and conflict without inventing legal authorities.\n"
        "- Use concrete sensory detail; avoid filler.\n"
        "- If legal themes appear, mark them as fiction, not advice.\n\n"
        "**Closing**\n"
        "- Resolve or leave a deliberate open question.\n\n"
        "_Creative scaffold — expand with a local/cloud model if configured._"
    )
    return ToolResult(True, "creative", "Creative writing", body, meta={"style": style})


def research_plan(query: str) -> ToolResult:
    q = (query or "").strip()
    body = (
        f"**Research plan**\n\n"
        f"**Query:** {q}\n\n"
        "1. Define jurisdiction and time frame.\n"
        "2. Identify official sources (BC Laws, court sites, CanLII) vs secondary commentary.\n"
        "3. Collect primary texts with currency lines / decision dates.\n"
        "4. Note treatment and hierarchy of authority.\n"
        "5. Extract pinpoints; flag anything UNVERIFIED.\n"
        "6. Human review before any filing or publication.\n\n"
        "Use `/v1/platform/ai/web-research` only for public non-confidential queries, "
        "or `/v1/platform/knowledge/bc-laws/fetch` for official statute HTML."
    )
    return ToolResult(True, "research_plan", "Research plan", body, meta={"query": q})


PRODUCTIVITY_TOOLS = {
    "summarize": summarize_text,
    "email_draft": draft_email,
    "creative": creative_writing,
    "research_plan": research_plan,
}
