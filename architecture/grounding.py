"""
GroundingGate contracts — every system claim must bind evidence + law + inference.

Refuse output if any required element is missing or broken.
Not legal advice; gate is a safety mechanism for workbench outputs.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from architecture.schemas import AuthorityStatus


class GroundingRefusalReason(str, Enum):
    MISSING_FACTUAL_BASIS = "MISSING_FACTUAL_BASIS"
    MISSING_LEGAL_BASIS = "MISSING_LEGAL_BASIS"
    BROKEN_INFERENCE_CHAIN = "BROKEN_INFERENCE_CHAIN"
    UNVERIFIED_CITATION = "UNVERIFIED_CITATION"
    REJECTED_CITATION = "REJECTED_CITATION"
    SUPERSEDED_CITATION = "SUPERSEDED_CITATION"
    EMPTY_CLAIM = "EMPTY_CLAIM"


REFUSAL_MESSAGES = {
    GroundingRefusalReason.MISSING_FACTUAL_BASIS: (
        "No evidence supports this claim. Add evidence or revise query."
    ),
    GroundingRefusalReason.MISSING_LEGAL_BASIS: (
        "No legal authority found. Search knowledge base or flag for human."
    ),
    GroundingRefusalReason.BROKEN_INFERENCE_CHAIN: (
        "Logical gap between evidence and conclusion. Review inference steps."
    ),
    GroundingRefusalReason.UNVERIFIED_CITATION: (
        "Legal authority is UNVERIFIED. Verify citation or flag for human."
    ),
    GroundingRefusalReason.REJECTED_CITATION: (
        "Legal authority is REJECTED. Remove or replace the citation."
    ),
    GroundingRefusalReason.SUPERSEDED_CITATION: (
        "Legal authority has been superseded. Use the replacing citation."
    ),
    GroundingRefusalReason.EMPTY_CLAIM: (
        "Empty claim. Provide a proposition to ground."
    ),
}


class CitationResolutionOption(str, Enum):
    """User/operator choices when a cite is not in the verified DB."""

    ADD_TO_DATABASE = "ADD_TO_DATABASE"  # requires source verification
    ILLUSTRATIVE_ONLY = "ILLUSTRATIVE_ONLY"  # flagged UNVERIFIED in output
    FIND_EQUIVALENT = "FIND_EQUIVALENT"  # use a verified substitute


@dataclass
class UnverifiedCitationFlag:
    """
    Structured flag when the reasoning engine wants a citation
    that is missing from or not VERIFIED in the citation database.
    """

    requested_reference: str  # case/section as requested
    in_database: bool
    database_status: Optional[str] = None  # UNVERIFIED | PARTIALLY_VERIFIED | missing
    citation_id: Optional[str] = None
    message: str = ""
    options: list[dict[str, str]] = field(default_factory=list)
    equivalent_candidates: list[dict[str, Any]] = field(default_factory=list)
    allows_illustrative_output: bool = True
    court_ready_allowed: bool = False  # always False for this flag

    def to_dict(self) -> dict[str, Any]:
        return {
            "flag": "UNVERIFIED_CITATION",
            "requested_reference": self.requested_reference,
            "in_database": self.in_database,
            "database_status": self.database_status,
            "citation_id": self.citation_id,
            "message": self.message,
            "options": list(self.options),
            "equivalent_candidates": list(self.equivalent_candidates),
            "allows_illustrative_output": self.allows_illustrative_output,
            "court_ready_allowed": self.court_ready_allowed,
        }

    def format_text(self) -> str:
        lines = [
            "UNVERIFIED CITATION FLAG:",
            self.message or (
                f'The reasoning engine wants to reference [{self.requested_reference}] but it '
                "does not exist in the verified citation database."
                if not self.in_database
                else (
                    f'The reasoning engine wants to reference [{self.requested_reference}] but it '
                    f"is not VERIFIED in the citation database "
                    f"(status={self.database_status})."
                )
            ),
            "",
            "Options:",
            "1. Add to database (requires source verification)",
            "2. Use as illustrative only (flagged in output as UNVERIFIED)",
            "3. Find equivalent verified citation",
        ]
        if self.equivalent_candidates:
            lines.append("")
            lines.append("Suggested equivalents (verified):")
            for eq in self.equivalent_candidates:
                cite = eq.get("short_cite") or eq.get("citation_id")
                tags = ", ".join(eq.get("applies_to") or [])
                lines.append(f"  - {cite}" + (f" [{tags}]" if tags else ""))
        lines.append("")
        lines.append(
            "Court-ready / GroundingGate output is blocked until option 1 (verified) "
            "or option 3 (substitute verified cite) is completed. "
            "Option 2 permits illustrative discussion only with an explicit UNVERIFIED flag."
        )
        return "\n".join(lines)


def build_unverified_citation_flag(
    requested: str,
    *,
    in_database: bool = False,
    database_status: Optional[str] = None,
    citation_id: Optional[str] = None,
    equivalents: Optional[list[dict[str, Any]]] = None,
) -> UnverifiedCitationFlag:
    if not in_database:
        msg = (
            f"The reasoning engine wants to reference [{requested}] but it "
            "does not exist in the verified citation database."
        )
    else:
        msg = (
            f"The reasoning engine wants to reference [{requested}] but it "
            f"is not VERIFIED in the citation database (status={database_status})."
        )
    options = [
        {
            "id": CitationResolutionOption.ADD_TO_DATABASE.value,
            "label": "Add to database (requires source verification)",
            "detail": (
                "Retrieve official text (BC Laws for statutes; CanLII/court for cases), "
                "set last_verified + verifying_hash, status=VERIFIED."
            ),
        },
        {
            "id": CitationResolutionOption.ILLUSTRATIVE_ONLY.value,
            "label": "Use as illustrative only (flagged in output as UNVERIFIED)",
            "detail": (
                "May appear in research notes with explicit UNVERIFIED marker. "
                "Must not appear in court-ready drafts or grounded claims."
            ),
        },
        {
            "id": CitationResolutionOption.FIND_EQUIVALENT.value,
            "label": "Find equivalent verified citation",
            "detail": (
                "Use a verified authority with overlapping applies_to tags "
                "or same subject matter; re-ground the claim on that cite."
            ),
        },
    ]
    return UnverifiedCitationFlag(
        requested_reference=requested,
        in_database=in_database,
        database_status=database_status,
        citation_id=citation_id,
        message=msg,
        options=options,
        equivalent_candidates=list(equivalents or []),
        allows_illustrative_output=True,
        court_ready_allowed=False,
    )


class CitationType(str, Enum):
    STATUTE = "STATUTE"
    REGULATION = "REGULATION"
    CASE_LAW = "CASE_LAW"
    RULE = "RULE"
    POLICY = "POLICY"


class JurisdictionScope(str, Enum):
    BC = "BC"
    CANADA = "CANADA"
    COMMONWEALTH = "COMMONWEALTH"
    OTHER = "OTHER"


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class Citation:
    """
    Full legal authority record for grounding and the verified citation DB.

    exact_text for statutes must be taken from BC Laws (or other official source)
    at verification time — do not invent statute wording.
    """

    citation_id: Optional[str] = None
    type: CitationType = CitationType.STATUTE

    # Statute / regulation
    jurisdiction: str = "BC"
    act: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    exact_text: Optional[str] = None  # official extract only; may be empty until verified

    # Case law
    case_name: Optional[str] = None
    citation: Optional[str] = None  # e.g. "[1982] 2 SCR 890"
    principle_established: Optional[str] = None
    parenthetical: Optional[str] = None

    # Verification
    source_url: Optional[str] = None
    last_verified: Optional[str] = None  # YYYY-MM-DD
    verifying_hash: Optional[str] = None  # sha256: of exact_text or registry blob
    superseded_by: Optional[str] = None  # citation_id

    # Usage constraints
    applies_to: list[str] = field(default_factory=list)
    jurisdiction_scope: JurisdictionScope = JurisdictionScope.BC

    # Workbench gate status (VERIFIED required for grounding)
    status: AuthorityStatus = AuthorityStatus.UNVERIFIED

    # Compatibility / display
    short_cite: Optional[str] = None
    official_title: Optional[str] = None
    neutral_citation: Optional[str] = None  # alias path for case law

    def display_cite(self) -> str:
        if self.short_cite:
            return self.short_cite
        if self.type == CitationType.CASE_LAW:
            if self.case_name and (self.citation or self.neutral_citation):
                return f"{self.case_name}, {self.citation or self.neutral_citation}"
            return self.case_name or self.citation or self.neutral_citation or self.citation_id or ""
        parts = []
        if self.act:
            # abbreviate common
            act = self.act
            if "Residential Tenancy Act" in act:
                act = "RTA"
            parts.append(act)
        if self.section:
            sec = f"s. {self.section}"
            if self.subsection:
                sec += f"({self.subsection})"
            parts.append(sec)
        return " ".join(parts) if parts else (self.citation_id or "")

    def ensure_ids_and_hash(self) -> None:
        if not self.citation_id:
            if self.type in (CitationType.STATUTE, CitationType.REGULATION) and self.section:
                act_key = "RTA" if self.act and "Residential Tenancy" in self.act else "ACT"
                if self.act and "Judicial Review" in self.act:
                    act_key = "JRPA"
                sub = f"-{self.subsection}" if self.subsection else ""
                self.citation_id = f"CIT-{act_key}-S{self.section}{sub}".replace(" ", "")
            elif self.type == CitationType.CASE_LAW and self.citation:
                slug = self.citation.replace("[", "").replace("]", "").replace(" ", "-")
                self.citation_id = f"CIT-{slug[:40]}"
            else:
                self.citation_id = f"CIT-{uuid4().hex[:10]}"
        if not self.short_cite:
            self.short_cite = self.display_cite()
        if self.citation and not self.neutral_citation:
            self.neutral_citation = self.citation
        if self.neutral_citation and not self.citation:
            self.citation = self.neutral_citation
        if self.exact_text and not self.verifying_hash:
            self.verifying_hash = _sha256_text(self.exact_text)

    def is_superseded(self) -> bool:
        return bool(self.superseded_by)

    def to_dict(self) -> dict[str, Any]:
        self.ensure_ids_and_hash()
        return {
            "citation_id": self.citation_id,
            "type": self.type.value,
            "jurisdiction": self.jurisdiction,
            "act": self.act,
            "section": self.section,
            "subsection": self.subsection,
            "exact_text": self.exact_text,
            "case_name": self.case_name,
            "citation": self.citation,
            "principle_established": self.principle_established,
            "parenthetical": self.parenthetical,
            "source_url": self.source_url,
            "last_verified": self.last_verified,
            "verifying_hash": self.verifying_hash,
            "superseded_by": self.superseded_by,
            "applies_to": list(self.applies_to),
            "jurisdiction_scope": self.jurisdiction_scope.value,
            "status": self.status.value,
            "short_cite": self.short_cite,
            "official_title": self.official_title,
            "neutral_citation": self.neutral_citation,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Citation":
        st = data.get("status", AuthorityStatus.UNVERIFIED.value)
        ctype = data.get("type", CitationType.STATUTE.value)
        jscope = data.get("jurisdiction_scope", JurisdictionScope.BC.value)
        # legacy short_cite-only rows
        short = data.get("short_cite")
        c = Citation(
            citation_id=data.get("citation_id"),
            type=CitationType(ctype) if not isinstance(ctype, CitationType) else ctype,
            jurisdiction=str(data.get("jurisdiction") or "BC"),
            act=data.get("act"),
            section=data.get("section"),
            subsection=data.get("subsection"),
            exact_text=data.get("exact_text"),
            case_name=data.get("case_name"),
            citation=data.get("citation") or data.get("neutral_citation"),
            principle_established=data.get("principle_established"),
            parenthetical=data.get("parenthetical"),
            source_url=data.get("source_url"),
            last_verified=data.get("last_verified"),
            verifying_hash=data.get("verifying_hash"),
            superseded_by=data.get("superseded_by"),
            applies_to=list(data.get("applies_to") or []),
            jurisdiction_scope=(
                JurisdictionScope(jscope)
                if not isinstance(jscope, JurisdictionScope)
                else jscope
            ),
            status=AuthorityStatus(st) if not isinstance(st, AuthorityStatus) else st,
            short_cite=short,
            official_title=data.get("official_title"),
            neutral_citation=data.get("neutral_citation") or data.get("citation"),
        )
        c.ensure_ids_and_hash()
        return c


@dataclass
class InferenceStep:
    """One explicit logical step connecting evidence to conclusion."""

    statement: str
    premise_type: str = "inference"  # fact | law | inference | conclusion
    supports_from: list[str] = field(default_factory=list)  # node_ids or citation_ids
    step_id: str = field(default_factory=lambda: str(uuid4())[:8])

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "statement": self.statement,
            "premise_type": self.premise_type,
            "supports_from": list(self.supports_from),
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "InferenceStep":
        return InferenceStep(
            statement=str(data.get("statement") or ""),
            premise_type=str(data.get("premise_type") or "inference"),
            supports_from=list(data.get("supports_from") or []),
            step_id=str(data.get("step_id") or str(uuid4())[:8]),
        )


@dataclass
class GroundedClaim:
    """A claim offered for GroundingGate evaluation."""

    claim: str
    factual_basis: Optional[str] = None  # EvidenceNode.node_id
    legal_basis: Optional[Citation] = None
    inference_chain: list[InferenceStep] = field(default_factory=list)
    claim_id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim": self.claim,
            "factual_basis": self.factual_basis,
            "legal_basis": self.legal_basis.to_dict() if self.legal_basis else None,
            "inference_chain": [s.to_dict() for s in self.inference_chain],
        }


@dataclass
class GroundingResult:
    allowed: bool
    claim: str
    reasons: list[GroundingRefusalReason] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    grounded: Optional[GroundedClaim] = None
    unverified_citation_flag: Optional[UnverifiedCitationFlag] = None
    illustrative_allowed: bool = False  # True only if UNVERIFIED flag path chosen for notes

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "claim": self.claim,
            "reasons": [r.value for r in self.reasons],
            "messages": list(self.messages),
            "grounded": self.grounded.to_dict() if self.grounded else None,
            "unverified_citation_flag": (
                self.unverified_citation_flag.to_dict()
                if self.unverified_citation_flag
                else None
            ),
            "illustrative_allowed": self.illustrative_allowed,
        }

    def refuse_text(self) -> str:
        if self.allowed:
            return ""
        parts = ["REFUSE_OUTPUT"] + [f"- {m}" for m in self.messages]
        if self.unverified_citation_flag:
            parts.append("")
            parts.append(self.unverified_citation_flag.format_text())
        return "\n".join(parts)
