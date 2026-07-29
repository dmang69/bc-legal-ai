"""Claude-inspired safety & reasoning gates for all assistant outputs.

Principles: helpful, honest, harmless — plus BC Legal fail-closed locks.
Never claims court-ready legal advice or autonomous filing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


DISALLOWED_PATTERNS = [
    (re.compile(r"\bthis is legal advice\b", re.I), "Claims to give legal advice"),
    (re.compile(r"\bi am (your|a) lawyer\b", re.I), "Impersonates a lawyer"),
    (re.compile(r"\bguaranteed (to )?win\b", re.I), "Guaranteed outcome"),
    (re.compile(r"\bfile this (today )?without review\b", re.I), "Bypasses human review"),
    (re.compile(r"\bignore (previous|all) instructions\b", re.I), "Prompt-injection style override"),
]

HARMFUL_INTENT = re.compile(
    r"\b(how to (make|build) (a )?bomb|child sexual|credit card fraud howto)\b",
    re.I,
)


@dataclass
class SafetyVerdict:
    allowed: bool
    reasons: list[str] = field(default_factory=list)
    rewritten_content: str = ""
    tags: list[str] = field(default_factory=list)
    court_ready: bool = False
    legal_advice: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reasons": self.reasons,
            "tags": self.tags,
            "court_ready": self.court_ready,
            "legal_advice": self.legal_advice,
        }


def assess_user_input(text: str) -> SafetyVerdict:
    if HARMFUL_INTENT.search(text or ""):
        return SafetyVerdict(
            allowed=False,
            reasons=["Request appears to seek clearly harmful assistance"],
            rewritten_content=(
                "I cannot help with that request. If you need legal information about "
                "a BC tenancy or judicial-review matter, rephrase with lawful, "
                "non-harmful intent. Not legal advice."
            ),
            tags=["blocked_harmful"],
        )
    return SafetyVerdict(allowed=True, tags=["input_ok"])


def enforce_output_safety(content: str, *, mode: str = "balanced") -> SafetyVerdict:
    """Post-process model output: strip false legal-advice claims; force disclaimers."""
    reasons: list[str] = []
    tags: list[str] = ["output_reviewed"]
    text = content or ""

    for pat, reason in DISALLOWED_PATTERNS:
        if pat.search(text):
            reasons.append(reason)
            tags.append("policy_rewrite")
            text = pat.sub("[removed: policy]", text)

    # Always append structural honesty footer for legal-adjacent modes
    footer_needed = "not legal advice" not in text.lower()
    if footer_needed:
        text = (
            text.rstrip()
            + "\n\n---\n"
            "**Safety & honesty:** Not legal advice. Not a lawyer. "
            "Outputs are WORKING DRAFTS — verify legislation on BC Laws, "
            "confirm facts against the record, and obtain supervising human approval "
            "before any filing or reliance. `court_ready: false`."
        )
        tags.append("disclaimer_appended")

    if mode == "deep":
        tags.append("extended_reasoning_encouraged")

    return SafetyVerdict(
        allowed=True,
        reasons=reasons,
        rewritten_content=text,
        tags=tags,
        court_ready=False,
        legal_advice=False,
    )


def reasoning_scaffold(question: str) -> str:
    """Claude-like structured thinking scaffold (shown to user as analysis frame)."""
    return (
        "### Structured reasoning frame\n"
        "1. **Clarify** the question and jurisdiction (default BC where legal).\n"
        "2. **Separate** FACT / ALLEGATION / LAW / ARGUMENT / INFERENCE / ASSUMPTION.\n"
        "3. **Identify** governing sources (statute, rule, case) — do not invent cites.\n"
        "4. **Consider** counter-arguments and ethical/privilege constraints.\n"
        "5. **State uncertainty** and what a human must verify.\n"
        "6. **Propose next steps** that preserve fail-closed gates.\n\n"
        f"**User question:** {question[:1500]}"
    )
