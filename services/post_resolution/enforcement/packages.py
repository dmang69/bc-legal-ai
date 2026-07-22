"""
Enforcement materials scaffold:
  - RTB enforcement application outline
  - Provincial Court monetary order filing package
  - Garnishment package (forms + affidavit outline)

Always use current official forms. Not legal advice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class PackageType(str, Enum):
    RTB_ENFORCEMENT = "RTB_ENFORCEMENT"
    PROVINCIAL_COURT_MONETARY = "PROVINCIAL_COURT_MONETARY"
    GARNISHMENT = "GARNISHMENT"


@dataclass
class PackageDocument:
    title: str
    doc_type: str  # form | affidavit | exhibit_list | cover
    status: str = "DRAFT_SCAFFOLD"
    body_outline: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "doc_type": self.doc_type,
            "status": self.status,
            "body_outline": list(self.body_outline),
        }


@dataclass
class EnforcementPackage:
    package_id: str
    matter_id: str
    package_type: PackageType
    documents: list[PackageDocument]
    checklist: list[str]
    created_at: str = field(default_factory=_utcnow)
    notes: str = "Scaffold only — download current forms from RTB / Provincial Court."

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "matter_id": self.matter_id,
            "package_type": self.package_type.value,
            "documents": [d.to_dict() for d in self.documents],
            "checklist": list(self.checklist),
            "created_at": self.created_at,
            "notes": self.notes,
        }


@dataclass
class EnforcementPackager:
    packages: list[EnforcementPackage] = field(default_factory=list)

    def build_rtb_enforcement(
        self,
        matter_id: str,
        *,
        order_summary: str = "",
        non_compliance_summary: str = "",
    ) -> EnforcementPackage:
        docs = [
            PackageDocument(
                title="RTB enforcement application outline",
                doc_type="form",
                body_outline=[
                    "Parties and file numbers",
                    f"Order to enforce: {order_summary or '[from decision]'}",
                    f"Non-compliance facts: {non_compliance_summary or '[evidence]'}",
                    "Remedy sought",
                    "Evidence list (node_ids / exhibits)",
                ],
            ),
            PackageDocument(
                title="Evidence index",
                doc_type="exhibit_list",
                body_outline=["Chronology", "Photos/receipts", "Prior order"],
            ),
        ]
        pkg = EnforcementPackage(
            package_id=f"ENF-{uuid4().hex[:10]}",
            matter_id=matter_id,
            package_type=PackageType.RTB_ENFORCEMENT,
            documents=docs,
            checklist=[
                "Confirm order finality and correct RTB process",
                "Current official form from gov.bc.ca",
                "Lawyer review before filing",
            ],
        )
        self.packages.append(pkg)
        return pkg

    def build_provincial_court_monetary(
        self,
        matter_id: str,
        *,
        amount: Optional[float] = None,
    ) -> EnforcementPackage:
        amt = f"${amount:,.2f}" if amount is not None else "[amount from order]"
        docs = [
            PackageDocument(
                title="Provincial Court monetary filing cover",
                doc_type="cover",
                body_outline=["Style of cause", f"Amount claimed: {amt}", "Basis: RTB order"],
            ),
            PackageDocument(
                title="Affidavit of non-payment (outline)",
                doc_type="affidavit",
                body_outline=[
                    "Deponent identity",
                    "Order date and amount",
                    "Non-payment facts",
                    "Exhibits: order, ledger, demands",
                ],
            ),
        ]
        pkg = EnforcementPackage(
            package_id=f"ENF-{uuid4().hex[:10]}",
            matter_id=matter_id,
            package_type=PackageType.PROVINCIAL_COURT_MONETARY,
            documents=docs,
            checklist=[
                "Confirm certification / registration path for RTB monetary orders",
                "Current Provincial Court forms",
                "Lawyer settle and swear affidavits",
            ],
        )
        self.packages.append(pkg)
        return pkg

    def build_garnishment(
        self,
        matter_id: str,
        *,
        debtor_name: str = "[debtor]",
    ) -> EnforcementPackage:
        docs = [
            PackageDocument(
                title="Garnishment forms checklist",
                doc_type="form",
                body_outline=[
                    f"Debtor: {debtor_name}",
                    "Identify garnishee (employer/bank) lawfully",
                    "Attach judgment/order",
                ],
            ),
            PackageDocument(
                title="Supporting affidavit outline",
                doc_type="affidavit",
                body_outline=[
                    "Debt amount and basis",
                    "Known income/assets sources (lawful knowledge only)",
                    "Prior enforcement steps",
                ],
            ),
        ]
        pkg = EnforcementPackage(
            package_id=f"ENF-{uuid4().hex[:10]}",
            matter_id=matter_id,
            package_type=PackageType.GARNISHMENT,
            documents=docs,
            checklist=[
                "BC garnishment rules and exemptions — counsel must confirm",
                "No fishing expeditions; privilege and privacy rules apply",
                "Lawyer review before any filing or service",
            ],
        )
        self.packages.append(pkg)
        return pkg
