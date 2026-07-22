"""Citation verification pipeline (Shepardizing-equivalent skeleton)."""

from knowledgebase.citation_verifier.pipeline import (
    CitationVerdict,
    VerifiedCitation,
    verify_citation,
    verify_text_citations,
)
from knowledgebase.citation_verifier.jurisdiction import JurisdictionWeight, weight_for_jurisdiction

__all__ = [
    "CitationVerdict",
    "VerifiedCitation",
    "verify_citation",
    "verify_text_citations",
    "JurisdictionWeight",
    "weight_for_jurisdiction",
]
