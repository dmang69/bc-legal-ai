"""
Chat / message privilege guard — detect third-party disclosure risk.

Scans user text before it is logged, sent, or used as matter notes.
Soft warn by default; does not replace lawyer judgment on privilege.
"""

from __future__ import annotations

import re
from typing import Optional

from architecture.privilege_alerts import (
    DEFAULT_THIRD_PARTY_ALERT_MESSAGE,
    THIRD_PARTY_ALERT_TEMPLATE,
    PrivilegeAlert,
    PrivilegeAlertKind,
    PrivilegeAlertSeverity,
)

# Non-party labels often implying no solicitor-client relationship
_THIRD_PARTY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("neighbor", re.compile(r"\b(neighbours?|neighbors?)\b", re.I)),
    ("friend", re.compile(r"\b(friends?|buddy|roommate'?s? friend)\b", re.I)),
    ("roommate", re.compile(r"\b(roommates?|housemates?)\b", re.I)),
    ("family member (non-client)", re.compile(r"\b(cousin|uncle|aunt|in-?laws?)\b", re.I)),
    ("coworker", re.compile(r"\b(coworkers?|colleagues?|boss|employer)\b", re.I)),
    ("landlord", re.compile(r"\b(landlords?|property manager)\b", re.I)),
    ("media", re.compile(r"\b(reporter|journalist|media|newspaper|tv news)\b", re.I)),
    ("social media", re.compile(r"\b(facebook|twitter|instagram|tiktok|posted online|social media)\b", re.I)),
    ("stranger / public", re.compile(r"\b(everyone|the public|strangers?)\b", re.I)),
]

# Verbs / context suggesting disclosure of case content
_DISCLOSURE_CONTEXT = re.compile(
    r"\b("
    r"told|tell|telling|talked|talking|talk|spoke|speaking|discuss(?:ed|ing)?|"
    r"shared|sharing|share|showed|showing|show|forwarded|forward|emailed|texted|"
    r"messaged|posted|posting|mentioned|mentioning|explained|explaining|"
    r"confided|confiding|asked .+ about (?:my|the) (?:case|eviction|hearing|rtb)"
    r")\b",
    re.I,
)

_CASE_CONTENT = re.compile(
    r"\b("
    r"case|eviction|hearing|arbitrator|rtb|petition|landlord|tenancy|dispute|"
    r"evidence|affidavit|transcript|privilege|strategy|legal advice|my lawyer|"
    r"counsel|court|stay|notice to end"
    r")\b",
    re.I,
)

# Parties usually inside privilege / professional circle (still contextual)
_LIKELY_PROTECTED = re.compile(
    r"\b(my lawyer|our lawyer|solicitor|barrister|legal aid|duty counsel|"
    r"articuling student at (?:the )?firm|paralegal at (?:the )?firm)\b",
    re.I,
)


def _find_third_parties(text: str) -> list[tuple[str, str]]:
    """Return list of (label, matched_span)."""
    hits: list[tuple[str, str]] = []
    for label, pat in _THIRD_PARTY_PATTERNS:
        m = pat.search(text)
        if m:
            hits.append((label, m.group(0)))
    return hits


def scan_message_for_privilege_risk(
    text: str,
    *,
    block_send: bool = False,
) -> Optional[PrivilegeAlert]:
    """
    If message suggests discussing case details with a non-party, return PrivilegeAlert.

    Special-case neighbor wording matches the principal's preferred alert copy.
    """
    if not text or not text.strip():
        return None

    # Skip pure questions about privilege law with no disclosure intent
    if _LIKELY_PROTECTED.search(text) and not _find_third_parties(text):
        return None

    parties = _find_third_parties(text)
    if not parties:
        return None

    has_disclosure = bool(_DISCLOSURE_CONTEXT.search(text))
    has_case = bool(_CASE_CONTENT.search(text))
    # Require an act of disclosure/sharing — not mere mention of landlord/neighbor as case actors
    if not has_disclosure:
        return None
    # Prefer case-related content; "I told my neighbor everything" still counts
    if not has_case and not re.search(
        r"\b(everything|details|what happened|my situation|the story)\b", text, re.I
    ):
        return None

    labels = [p[0] for p in parties]
    triggers = [p[1] for p in parties]
    m = _DISCLOSURE_CONTEXT.search(text)
    if m:
        triggers.append(m.group(0))

    # Preferred copy when neighbor is the third party
    if any(p[0] == "neighbor" for p in parties):
        message = DEFAULT_THIRD_PARTY_ALERT_MESSAGE
        party_phrase = "your neighbor"
    else:
        party_phrase = labels[0]
        message = THIRD_PARTY_ALERT_TEMPLATE.format(party=party_phrase)

    return PrivilegeAlert(
        kind=PrivilegeAlertKind.THIRD_PARTY_DISCLOSURE,
        severity=PrivilegeAlertSeverity.WARNING,
        title="PRIVILEGE ALERT",
        message=message,
        triggers=triggers,
        third_parties_mentioned=labels,
        recommendations=[
            "Do not share litigation strategy, unfiled evidence, or lawyer communications with non-parties.",
            "If you already disclosed, note what was said, to whom, and when — for counsel review.",
            "Prefer discussing the case only with your lawyer (or authorized team) and necessary witnesses as advised by counsel.",
            "Social media and group chats are high-risk for unintended waiver and publicity.",
        ],
        block_send=block_send,
        requires_ack=True,
    )


def guard_user_message(
    text: str,
    *,
    block_send: bool = False,
) -> dict:
    """
    Convenience API for UI/chat layer.

    Returns { allowed, alert, alert_text }.
    """
    alert = scan_message_for_privilege_risk(text, block_send=block_send)
    if alert is None:
        return {"allowed": True, "alert": None, "alert_text": None}
    allowed = not block_send  # soft warn still allows continue after ack
    if block_send:
        allowed = False
    return {
        "allowed": allowed,
        "alert": alert.to_dict(),
        "alert_text": alert.format_alert(),
        "requires_ack": alert.requires_ack,
    }
