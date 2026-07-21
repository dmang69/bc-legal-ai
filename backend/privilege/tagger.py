"""
Privilege Tagger — Stage 1–2 rule first-pass.

Does not finalize. Confidence < 0.85 or third-party channels force human review.
"""

from __future__ import annotations

from architecture.privilege_schemas import (
    HUMAN_REVIEW_CONFIDENCE_THRESHOLD,
    PartyCommRole,
    PrivilegeBasis,
    PrivilegeTagProposal,
)


def propose_privilege_tag(
    *,
    sender_role: PartyCommRole,
    recipient_role: PartyCommRole,
    advice_sought: bool,
    advice_given: bool,
    litigation_context: bool,
    confidence: float,
) -> PrivilegeTagProposal:
    """Stage 2 rule assignment + Stage 3 review flags."""
    lawyer_client = {PartyCommRole.CLIENT, PartyCommRole.LAWYER}
    channel_ok = sender_role in lawyer_client and recipient_role in lawyer_client
    third_party = (
        PartyCommRole.THIRD_PARTY in (sender_role, recipient_role)
        or PartyCommRole.UNKNOWN in (sender_role, recipient_role)
    )
    advice_or_lit = advice_sought or advice_given or litigation_context

    if channel_ok and advice_or_lit and not third_party:
        if litigation_context and not (advice_sought or advice_given):
            basis = PrivilegeBasis.LITIGATION
        else:
            basis = PrivilegeBasis.SOLICITOR_CLIENT
    else:
        basis = PrivilegeBasis.NONE

    # Conservative confidence adjustments (rule-based until NLI model exists)
    adj = confidence
    if third_party:
        adj = min(adj, 0.7)
    if sender_role == PartyCommRole.UNKNOWN or recipient_role == PartyCommRole.UNKNOWN:
        adj = min(adj, 0.6)

    needs_review = adj < HUMAN_REVIEW_CONFIDENCE_THRESHOLD or third_party or basis != PrivilegeBasis.NONE

    return PrivilegeTagProposal(
        sender_role=sender_role,
        recipient_role=recipient_role,
        advice_sought=advice_sought,
        advice_given=advice_given,
        litigation_context=litigation_context,
        proposed_basis=basis,
        confidence=adj,
        requires_human_review=needs_review,
        finalized=False,
    )
