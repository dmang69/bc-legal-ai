"""
Section-topic validation for LegalTest registry entries.

A test must fail when configured topic and official section heading
are materially inconsistent. Not legal advice — headings must be
verified on BC Laws.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SectionTopicRecord:
    act: str
    section: str
    section_heading: str  # from official source / registry
    source_url: str
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    source_hash: Optional[str] = None
    expected_legal_topic: str = ""
    human_verifier: Optional[str] = None
    verified_at: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "act": self.act,
            "section": self.section,
            "section_heading": self.section_heading,
            "source_url": self.source_url,
            "effective_from": self.effective_from,
            "effective_to": self.effective_to,
            "source_hash": self.source_hash,
            "expected_legal_topic": self.expected_legal_topic,
            "human_verifier": self.human_verifier,
            "verified_at": self.verified_at,
        }


@dataclass
class SectionTopicResult:
    ok: bool
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "reasons": list(self.reasons)}


# Known mismatches (fail closed)
KNOWN_MISMATCHES: list[tuple[str, str, str]] = [
    # (act_contains, section, forbidden_topic_substring)
    ("residential tenancy", "56", "retaliat"),
]


def validate_section_topic(record: SectionTopicRecord) -> SectionTopicResult:
    reasons: list[str] = []
    if not record.act.strip():
        reasons.append("Act name required")
    if not record.section.strip():
        reasons.append("Section number required")
    if not record.section_heading.strip():
        reasons.append("Section heading required (from official source)")
    if not record.source_url.strip():
        reasons.append("Source URL required")
    if not record.expected_legal_topic.strip():
        reasons.append("Expected legal topic required")

    act_l = record.act.lower()
    heading_l = record.section_heading.lower()
    topic_l = record.expected_legal_topic.lower()
    sec = record.section.strip().lstrip("s.S. ").split("(")[0]

    for act_key, section, forbidden in KNOWN_MISMATCHES:
        if act_key in act_l and sec == section and forbidden in topic_l:
            reasons.append(
                f"Topic '{record.expected_legal_topic}' is inconsistent with known "
                f"mapping for {record.act} s.{section} "
                f"(heading currently registered as: {record.section_heading!r}). "
                "Re-verify on BC Laws before activating any LegalTest."
            )

    # Soft check: if heading contains words that contradict topic
    if "retaliat" in topic_l and "early" in heading_l and "end" in heading_l:
        reasons.append(
            "Topic suggests retaliation but heading suggests early end of tenancy — mismatch."
        )

    if not record.human_verifier:
        reasons.append("human_verifier required before ACTIVE status")

    return SectionTopicResult(ok=len(reasons) == 0, reasons=reasons)


# Seeded official heading for RTA s.56 (confirm on BC Laws before production use)
RTA_S56_REGISTRY = SectionTopicRecord(
    act="Residential Tenancy Act, SBC 2002, c 78",
    section="56",
    section_heading="Application for order ending tenancy early (confirm current heading on BC Laws)",
    source_url="https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/02078_01",
    expected_legal_topic="retaliatory_eviction",  # intentionally wrong for test of validator
    human_verifier=None,
)
