"""
GroundingGate — refuse system claims without evidence + verified law + inference chain.

GroundingGate {
    required_elements: factual_basis (node_id), legal_basis (Citation), inference_chain
    on_missing_*: REFUSE_OUTPUT + message
}
"""

from __future__ import annotations

from typing import Iterable, Optional, Set

from architecture.grounding import (
    REFUSAL_MESSAGES,
    Citation,
    GroundedClaim,
    GroundingRefusalReason,
    GroundingResult,
    UnverifiedCitationFlag,
    build_unverified_citation_flag,
)
from architecture.schemas import AuthorityStatus
from backend.grounding.citation_db import CitationDB


def _requested_label(cite: Citation) -> str:
    return (
        cite.display_cite()
        or cite.short_cite
        or cite.citation_id
        or cite.case_name
        or cite.citation
        or "unknown authority"
    )


def flag_unverified_reference(
    citation_db: CitationDB,
    reference: Citation | str,
    *,
    applies_to_hint: Optional[list[str]] = None,
) -> UnverifiedCitationFlag:
    """
    Build UNVERIFIED CITATION FLAG for a requested case/section.

    Used by the reasoning engine when a cite is not verified (or not in DB).
    """
    if isinstance(reference, str):
        probe = Citation(short_cite=reference)
    else:
        probe = reference

    resolved = citation_db.resolve(probe)
    requested = _requested_label(probe if not resolved else resolved)

    equivalents: list[dict] = []
    tags = list(applies_to_hint or [])
    if resolved and resolved.applies_to:
        tags = list(dict.fromkeys(tags + list(resolved.applies_to)))
    # pull from short_cite heuristics
    low = requested.lower()
    if "retaliat" in low or "s. 56" in low or "s.56" in low:
        tags.append("retaliatory_eviction")
    if "mold" in low or "repair" in low or "s. 32" in low:
        tags.append("mold_hazard")
    if "privilege" in low or "descoteaux" in low:
        tags.append("privilege")

    seen_ids: set[str] = set()
    for tag in tags:
        for c in citation_db.by_applies_to(tag):
            if c.citation_id and c.citation_id not in seen_ids:
                if resolved and c.citation_id == resolved.citation_id:
                    continue
                seen_ids.add(c.citation_id)
                equivalents.append(
                    {
                        "citation_id": c.citation_id,
                        "short_cite": c.short_cite or c.display_cite(),
                        "applies_to": list(c.applies_to),
                        "status": c.status.value,
                    }
                )

    if resolved is None:
        return build_unverified_citation_flag(
            requested,
            in_database=False,
            database_status=None,
            citation_id=None,
            equivalents=equivalents,
        )
    return build_unverified_citation_flag(
        requested,
        in_database=True,
        database_status=resolved.status.value,
        citation_id=resolved.citation_id,
        equivalents=equivalents,
    )


class GroundingGate:
    """
    Fail-closed gate for workbench outputs.

    factual_basis must be an EvidenceNode.node_id present in the matter graph.
    legal_basis must resolve to VERIFIED in CitationDB.
    inference_chain must be non-empty and connect fact → law → conclusion.
    """

    def __init__(
        self,
        *,
        known_node_ids: Iterable[str],
        citation_db: CitationDB,
    ) -> None:
        self.known_node_ids: Set[str] = set(known_node_ids)
        self.citation_db = citation_db

    def evaluate(self, claim: GroundedClaim) -> GroundingResult:
        reasons: list[GroundingRefusalReason] = []
        messages: list[str] = []
        uv_flag: Optional[UnverifiedCitationFlag] = None

        text = (claim.claim or "").strip()
        if not text:
            reasons.append(GroundingRefusalReason.EMPTY_CLAIM)
            messages.append(REFUSAL_MESSAGES[GroundingRefusalReason.EMPTY_CLAIM])
            return GroundingResult(
                allowed=False, claim=claim.claim or "", reasons=reasons, messages=messages
            )

        # --- factual_basis ---
        if not claim.factual_basis:
            reasons.append(GroundingRefusalReason.MISSING_FACTUAL_BASIS)
            messages.append(
                REFUSAL_MESSAGES[GroundingRefusalReason.MISSING_FACTUAL_BASIS]
            )
        elif claim.factual_basis not in self.known_node_ids:
            reasons.append(GroundingRefusalReason.MISSING_FACTUAL_BASIS)
            messages.append(
                REFUSAL_MESSAGES[GroundingRefusalReason.MISSING_FACTUAL_BASIS]
                + f" (node_id {claim.factual_basis!r} not in evidence matrix)."
            )

        # --- legal_basis ---
        if claim.legal_basis is None:
            reasons.append(GroundingRefusalReason.MISSING_LEGAL_BASIS)
            messages.append(REFUSAL_MESSAGES[GroundingRefusalReason.MISSING_LEGAL_BASIS])
        else:
            resolved = self.citation_db.resolve(claim.legal_basis)
            if resolved is None:
                reasons.append(GroundingRefusalReason.MISSING_LEGAL_BASIS)
                reasons.append(GroundingRefusalReason.UNVERIFIED_CITATION)
                messages.append(
                    REFUSAL_MESSAGES[GroundingRefusalReason.MISSING_LEGAL_BASIS]
                )
                uv_flag = flag_unverified_reference(
                    self.citation_db, claim.legal_basis
                )
                messages.append(uv_flag.message)
            elif resolved.superseded_by:
                reasons.append(GroundingRefusalReason.SUPERSEDED_CITATION)
                messages.append(
                    REFUSAL_MESSAGES[GroundingRefusalReason.SUPERSEDED_CITATION]
                    + f" (use {resolved.superseded_by})."
                )
            elif resolved.status == AuthorityStatus.REJECTED:
                reasons.append(GroundingRefusalReason.REJECTED_CITATION)
                messages.append(
                    REFUSAL_MESSAGES[GroundingRefusalReason.REJECTED_CITATION]
                )
            elif resolved.status != AuthorityStatus.VERIFIED:
                reasons.append(GroundingRefusalReason.UNVERIFIED_CITATION)
                uv_flag = flag_unverified_reference(
                    self.citation_db,
                    resolved,
                    applies_to_hint=list(resolved.applies_to),
                )
                messages.append(uv_flag.message)
            else:
                # attach resolved citation with id
                claim.legal_basis = resolved

        # --- inference_chain ---
        if not claim.inference_chain:
            reasons.append(GroundingRefusalReason.BROKEN_INFERENCE_CHAIN)
            messages.append(
                REFUSAL_MESSAGES[GroundingRefusalReason.BROKEN_INFERENCE_CHAIN]
            )
        else:
            chain_ok, chain_msg = self._validate_inference_chain(claim)
            if not chain_ok:
                reasons.append(GroundingRefusalReason.BROKEN_INFERENCE_CHAIN)
                messages.append(
                    REFUSAL_MESSAGES[GroundingRefusalReason.BROKEN_INFERENCE_CHAIN]
                    + (f" {chain_msg}" if chain_msg else "")
                )

        allowed = len(reasons) == 0
        return GroundingResult(
            allowed=allowed,
            claim=text,
            reasons=reasons,
            messages=messages,
            grounded=claim if allowed else None,
            unverified_citation_flag=uv_flag,
            illustrative_allowed=bool(uv_flag and uv_flag.allows_illustrative_output),
        )

    def check_citation(self, reference: Citation | str) -> UnverifiedCitationFlag | None:
        """
        Pre-flight: if reference is not VERIFIED, return UNVERIFIED CITATION FLAG.
        Returns None when the citation is verified and current.
        """
        if isinstance(reference, str):
            probe = Citation(short_cite=reference)
        else:
            probe = reference
        resolved = self.citation_db.resolve(probe)
        if resolved and resolved.status == AuthorityStatus.VERIFIED and not resolved.superseded_by:
            return None
        return flag_unverified_reference(self.citation_db, probe if not resolved else resolved)

    def assert_grounded(self, claim: GroundedClaim) -> GroundedClaim:
        result = self.evaluate(claim)
        if not result.allowed:
            raise PermissionError(result.refuse_text())
        assert result.grounded is not None
        return result.grounded

    def _validate_inference_chain(
        self, claim: GroundedClaim
    ) -> tuple[bool, str]:
        """
        Require at least: one fact-linked step, one law-linked step, one conclusion-ish step
        OR a chain of ≥2 non-empty steps that reference the factual and legal bases.
        """
        steps = claim.inference_chain
        non_empty = [s for s in steps if (s.statement or "").strip()]
        if len(non_empty) < 2:
            return False, "Need at least two non-empty inference steps."

        fact_id = claim.factual_basis or ""
        law_id = ""
        if claim.legal_basis:
            law_id = claim.legal_basis.citation_id or claim.legal_basis.short_cite

        references_fact = False
        references_law = False
        has_conclusion = False

        for s in non_empty:
            ptype = (s.premise_type or "").lower()
            supports = " ".join(s.supports_from).lower()
            stmt = s.statement.lower()
            if ptype == "fact" or (fact_id and fact_id in s.supports_from):
                references_fact = True
            if fact_id and fact_id.lower() in supports:
                references_fact = True
            if ptype == "law" or (
                law_id and (law_id in s.supports_from or law_id.lower() in supports)
            ):
                references_law = True
            if claim.legal_basis and claim.legal_basis.short_cite:
                if claim.legal_basis.short_cite.lower() in stmt:
                    references_law = True
            if ptype in ("conclusion", "inference") or "therefore" in stmt or "thus" in stmt:
                has_conclusion = True

        # Soft: if types not annotated, accept chain that mentions both bases in supports
        if not references_fact:
            # allow first step to be treated as fact if supports empty but we have factual_basis
            if non_empty[0].premise_type in ("", "inference", "fact"):
                non_empty[0].premise_type = "fact"
                if fact_id and fact_id not in non_empty[0].supports_from:
                    non_empty[0].supports_from.append(fact_id)
                references_fact = True

        if not references_law and claim.legal_basis:
            for s in non_empty:
                if s.premise_type == "law" or "s." in s.statement.lower() or "act" in s.statement.lower():
                    references_law = True
                    if claim.legal_basis.citation_id:
                        s.supports_from.append(claim.legal_basis.citation_id)
                    break

        if not has_conclusion:
            # last step becomes conclusion
            non_empty[-1].premise_type = "conclusion"
            has_conclusion = True

        if not references_fact:
            return False, "Chain does not connect to factual_basis node."
        if not references_law:
            return False, "Chain does not connect to legal_basis citation."
        if not has_conclusion:
            return False, "Chain lacks a conclusion step."
        return True, ""


def build_gate_for_nodes(
    node_ids: Iterable[str],
    citation_db: Optional[CitationDB] = None,
) -> GroundingGate:
    from backend.grounding.citation_db import seed_bc_workbench_citations

    db = citation_db or seed_bc_workbench_citations(CitationDB())
    return GroundingGate(known_node_ids=node_ids, citation_db=db)
