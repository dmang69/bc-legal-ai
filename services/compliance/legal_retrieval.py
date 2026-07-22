"""
Fail-closed legal text retrieval — BC Laws only for BC statutes.

Never return statute text from model memory or CanLII for court packages.
Not legal advice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SourcePolicy(str, Enum):
    BC_LAWS_ONLY = "BC_LAWS_ONLY"
    CANLII_CASES_ONLY = "CANLII_CASES_ONLY"
    REJECTED = "REJECTED"


ALLOWED_STATUTE_HOSTS = (
    "www.bclaws.gov.bc.ca",
    "bclaws.gov.bc.ca",
)

# CanLII allowed for decisions only — never as statute source
CANLII_HOSTS = ("www.canlii.org", "canlii.org")


@dataclass
class RetrievalDecision:
    allowed: bool
    policy: SourcePolicy
    reason: str
    redirect_url: Optional[str] = None
    currency_check_required: bool = True

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "policy": self.policy.value,
            "reason": self.reason,
            "redirect_url": self.redirect_url,
            "currency_check_required": self.currency_check_required,
        }


@dataclass
class FailClosedRetrieval:
    """Gate any request for legal text before it reaches a model or cache."""

    def authorize_statute_text(
        self,
        *,
        source_url: Optional[str] = None,
        from_model_weights: bool = False,
        from_canlii: bool = False,
    ) -> RetrievalDecision:
        if from_model_weights:
            return RetrievalDecision(
                allowed=False,
                policy=SourcePolicy.REJECTED,
                reason="Statute text must not be quoted from model weights. Open BC Laws.",
                redirect_url="https://www.bclaws.gov.bc.ca/",
            )
        if from_canlii:
            return RetrievalDecision(
                allowed=False,
                policy=SourcePolicy.REJECTED,
                reason="CanLII is not an official source for BC statute text in court packages.",
                redirect_url="https://www.bclaws.gov.bc.ca/",
            )
        if not source_url:
            return RetrievalDecision(
                allowed=False,
                policy=SourcePolicy.REJECTED,
                reason="No official source URL. Fail-closed.",
                redirect_url="https://www.bclaws.gov.bc.ca/",
            )
        host = source_url.split("/")[2].lower() if "://" in source_url else ""
        if host in ALLOWED_STATUTE_HOSTS or host.endswith(".bclaws.gov.bc.ca"):
            return RetrievalDecision(
                allowed=True,
                policy=SourcePolicy.BC_LAWS_ONLY,
                reason="BC Laws host authorized. Re-check 'current to' line before filing.",
                redirect_url=source_url,
            )
        return RetrievalDecision(
            allowed=False,
            policy=SourcePolicy.REJECTED,
            reason=f"Host not authorized for statute text: {host or 'unknown'}",
            redirect_url="https://www.bclaws.gov.bc.ca/",
        )

    def authorize_case_citation(self, *, source_url: Optional[str] = None) -> RetrievalDecision:
        if not source_url:
            return RetrievalDecision(
                allowed=False,
                policy=SourcePolicy.REJECTED,
                reason="Case citation requires a verifiable source URL (e.g. CanLII).",
            )
        host = source_url.split("/")[2].lower() if "://" in source_url else ""
        if host in CANLII_HOSTS or "courts.gov.bc.ca" in host:
            return RetrievalDecision(
                allowed=True,
                policy=SourcePolicy.CANLII_CASES_ONLY,
                reason="Case source host allowed for decisions only.",
                redirect_url=source_url,
                currency_check_required=False,
            )
        return RetrievalDecision(
            allowed=False,
            policy=SourcePolicy.REJECTED,
            reason=f"Case host not recognized: {host or 'unknown'}",
        )
