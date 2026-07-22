"""Jurisdiction flagging — Ontario persuasive, BC binding (where applicable)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class JurisdictionWeight(str, Enum):
    BINDING = "BINDING"
    PERSUASIVE = "PERSUASIVE"
    FOREIGN = "FOREIGN"
    UNKNOWN = "UNKNOWN"


@dataclass
class JurisdictionFlag:
    jurisdiction: str
    weight: JurisdictionWeight
    note: str

    def to_dict(self) -> dict:
        return {
            "jurisdiction": self.jurisdiction,
            "weight": self.weight.value,
            "note": self.note,
        }


def weight_for_jurisdiction(jurisdiction: str) -> JurisdictionFlag:
    j = (jurisdiction or "").upper().strip()
    if j in ("BC", "B.C.", "BRITISH COLUMBIA", "BCCA", "BCSC", "BCPC", "RTB"):
        return JurisdictionFlag(
            jurisdiction=j or "BC",
            weight=JurisdictionWeight.BINDING,
            note="BC authority — potentially binding depending on court hierarchy and issue.",
        )
    if j in ("SCC", "SUPREME COURT OF CANADA", "CANADA"):
        return JurisdictionFlag(
            jurisdiction=j,
            weight=JurisdictionWeight.BINDING,
            note="SCC is binding on all Canadian courts on federal/constitutional issues engaged.",
        )
    if j in ("ON", "ONTARIO", "ONCA", "ONSC", "AB", "ABCA", "QC", "NS", "MB", "SK"):
        return JurisdictionFlag(
            jurisdiction=j,
            weight=JurisdictionWeight.PERSUASIVE,
            note="Extra-provincial Canadian authority is generally persuasive, not binding in BC.",
        )
    if j in ("UK", "US", "AUS", "NZ"):
        return JurisdictionFlag(
            jurisdiction=j,
            weight=JurisdictionWeight.FOREIGN,
            note="Foreign authority — use only with care; not binding.",
        )
    return JurisdictionFlag(
        jurisdiction=j or "UNKNOWN",
        weight=JurisdictionWeight.UNKNOWN,
        note="Jurisdiction not classified — human review required.",
    )
