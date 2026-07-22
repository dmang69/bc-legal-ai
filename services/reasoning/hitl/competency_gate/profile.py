from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class PracticeArea(str, Enum):
    RESIDENTIAL_TENANCY = "RESIDENTIAL_TENANCY"
    ADMINISTRATIVE_LAW = "ADMINISTRATIVE_LAW"
    CIVIL_LITIGATION = "CIVIL_LITIGATION"
    JUDICIAL_REVIEW = "JUDICIAL_REVIEW"
    HUMAN_RIGHTS = "HUMAN_RIGHTS"
    CORPORATE = "CORPORATE"
    FAMILY = "FAMILY"
    CRIMINAL = "CRIMINAL"
    PRIVACY_REGULATORY = "PRIVACY_REGULATORY"
    OTHER = "OTHER"


@dataclass
class CurrencyRecord:
    subject: str  # RTA amendments | RTB Rules | RTB forms | JRPA | SCR
    verified_at: str

    def to_dict(self) -> dict[str, Any]:
        return {"subject": self.subject, "verified_at": self.verified_at}


@dataclass
class LawyerProfile:
    lawyer_id: str
    name: str
    licensing_jurisdictions: list[str] = field(default_factory=list)
    licence_status: str = "unknown"  # ACTIVE | SUSPENDED | unknown
    practice_areas: list[str] = field(default_factory=list)
    procedural_permissions: list[str] = field(default_factory=list)  # RTB | BC_SUPREME_COURT
    currency_records: list[CurrencyRecord] = field(default_factory=list)
    conflict_status: str = "UNKNOWN"  # CLEAR | POTENTIAL | CONFIRMED_CONFLICT
    conflict_cleared_matters: list[str] = field(default_factory=list)
    approval_limits: list[str] = field(default_factory=list)
    backup_reviewer_id: Optional[str] = None
    # legacy fields
    jurisdictions: list[str] = field(default_factory=list)
    bar_status: str = "unknown"
    statute_currency_ack: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.licensing_jurisdictions and self.jurisdictions:
            self.licensing_jurisdictions = list(self.jurisdictions)
        if self.jurisdictions != self.licensing_jurisdictions:
            self.jurisdictions = list(self.licensing_jurisdictions)
        if self.licence_status == "unknown" and self.bar_status != "unknown":
            self.licence_status = "ACTIVE" if self.bar_status == "active" else self.bar_status.upper()
        if self.bar_status == "unknown" and self.licence_status != "unknown":
            self.bar_status = self.licence_status.lower() if self.licence_status == "ACTIVE" else self.licence_status.lower()
        if self.statute_currency_ack and not self.currency_records:
            self.currency_records = [
                CurrencyRecord(subject="RTA amendments", verified_at=self.statute_currency_ack)
            ]
