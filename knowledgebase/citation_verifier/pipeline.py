"""
Verify citations against primary source DB; treatment / Shepardizing stub.

Fail-closed: unknown cites → UNVERIFIED. Never invent treatment.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from knowledgebase.citation_verifier.jurisdiction import (
    JurisdictionFlag,
    weight_for_jurisdiction,
)
from knowledgebase.primary_sources import PrimarySourceRegistry, SourceRecord


class CitationVerdict(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    REJECTED = "REJECTED"


@dataclass
class TreatmentNote:
    """Shepardizing-equivalent — stub until CanLII treatment API licensed."""

    status: str  # GOOD_LAW | DISTINGUISHED | OVERRULED | UNKNOWN
    note: str = "Treatment not auto-fetched. Confirm on CanLII / official reporter."

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "note": self.note}


@dataclass
class VerifiedCitation:
    raw: str
    verdict: CitationVerdict
    matched_source_id: Optional[str] = None
    official_url: Optional[str] = None
    jurisdiction: Optional[JurisdictionFlag] = None
    treatment: TreatmentNote = field(
        default_factory=lambda: TreatmentNote(status="UNKNOWN")
    )
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw": self.raw,
            "verdict": self.verdict.value,
            "matched_source_id": self.matched_source_id,
            "official_url": self.official_url,
            "jurisdiction": self.jurisdiction.to_dict() if self.jurisdiction else None,
            "treatment": self.treatment.to_dict(),
            "reasons": list(self.reasons),
        }


# Common RTA pins from verification log (re-check BC Laws before filing)
_RTA_PINS = {
    "s. 5", "s.5", "s. 6", "s.6", "s. 15", "s. 19", "s. 20", "s. 22",
    "s. 28", "s. 29", "s. 32", "s. 33", "s. 38", "s. 42", "s. 43",
}


def verify_citation(
    raw: str,
    *,
    registry: Optional[PrimarySourceRegistry] = None,
    jurisdiction_hint: str = "BC",
) -> VerifiedCitation:
    registry = registry or PrimarySourceRegistry()
    text = (raw or "").strip()
    if not text:
        return VerifiedCitation(
            raw=raw,
            verdict=CitationVerdict.REJECTED,
            reasons=["Empty citation"],
        )

    jflag = weight_for_jurisdiction(jurisdiction_hint)
    low = text.lower()

    # Statute match against registry titles / citations
    for rec in registry.records:
        if rec.kind != "statute":
            continue
        if rec.citation.lower() in low or rec.title.lower()[:40] in low:
            return VerifiedCitation(
                raw=raw,
                verdict=CitationVerdict.PARTIALLY_VERIFIED,
                matched_source_id=rec.source_id,
                official_url=rec.official_url,
                jurisdiction=jflag,
                treatment=TreatmentNote(
                    status="UNKNOWN",
                    note="Statute source known — re-open BC Laws; check 'current to' and point-in-time.",
                ),
                reasons=["Matched primary source registry entry", "Pinpoint not auto-verified"],
            )

    # RTA section pin shorthand
    pin_m = re.search(r"\bs\.?\s*(\d+[a-z]?)\b", low)
    if pin_m and ("rta" in low or "residential tenancy" in low or re.match(r"^s\.?\s*\d", low)):
        pin = f"s. {pin_m.group(1)}"
        rta = registry.get("RTA-SBC-2002-c78")
        if pin in _RTA_PINS or f"s.{pin_m.group(1)}" in _RTA_PINS:
            return VerifiedCitation(
                raw=raw,
                verdict=CitationVerdict.PARTIALLY_VERIFIED,
                matched_source_id=rta.source_id if rta else None,
                official_url=rta.official_url if rta else None,
                jurisdiction=weight_for_jurisdiction("BC"),
                reasons=[
                    f"Known RTA pin map entry for {pin}",
                    "Still re-verify full section text on BC Laws before filing",
                ],
            )

    # Ontario etc. case cite heuristic
    if re.search(r"\b(onca|ont\.?\s*c\.?a|ontario)\b", low):
        jflag = weight_for_jurisdiction("ON")
        return VerifiedCitation(
            raw=raw,
            verdict=CitationVerdict.UNVERIFIED,
            jurisdiction=jflag,
            reasons=["Ontario authority flagged as persuasive only for BC matters"],
        )

    return VerifiedCitation(
        raw=raw,
        verdict=CitationVerdict.UNVERIFIED,
        jurisdiction=jflag,
        reasons=["No registry match — do not use in court-ready mode"],
    )


_CITE_SPLIT = re.compile(
    r"(?:Residential Tenancy Act[^.]*|RTA\s*s\.?\s*\d+|s\.\s*\d+\s*(?:RTA)?|"
    r"Vavilov|JRPA|Judicial Review Procedure Act)",
    re.I,
)


def verify_text_citations(
    text: str,
    *,
    registry: Optional[PrimarySourceRegistry] = None,
) -> list[VerifiedCitation]:
    found = _CITE_SPLIT.findall(text or "")
    if not found:
        return []
    return [verify_citation(c, registry=registry) for c in found]
