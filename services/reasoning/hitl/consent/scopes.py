"""
Purpose-specific consent categories (Phase 3.1A).

Processing consent ≠ privilege waiver. External model requires separate category.
"""

from __future__ import annotations

from enum import Enum


class ConsentScope(str, Enum):
    """Canonical categories + legacy aliases (same values)."""

    GENERAL_MATTER_DATA = "GENERAL_MATTER_DATA"
    TENANCY_RECORDS = "TENANCY_RECORDS"
    FINANCIAL_INFORMATION = "FINANCIAL_INFORMATION"
    MEDICAL_INFORMATION = "MEDICAL_INFORMATION"
    DISABILITY_INFORMATION = "DISABILITY_INFORMATION"
    PHOTOGRAPHS = "PHOTOGRAPHS"
    AUDIO_RECORDINGS = "AUDIO_RECORDINGS"
    VIDEO_RECORDINGS = "VIDEO_RECORDINGS"
    LOCATION_METADATA = "LOCATION_METADATA"
    EMAIL_IMPORT = "EMAIL_IMPORT"
    CLOUD_STORAGE_IMPORT = "CLOUD_STORAGE_IMPORT"
    AI_ANALYSIS = "AI_ANALYSIS"
    EXTERNAL_MODEL_PROCESSING = "EXTERNAL_MODEL_PROCESSING"
    ANONYMIZED_EVALUATION = "ANONYMIZED_EVALUATION"
    CLIENT_COMMUNICATION_ANALYSIS = "CLIENT_COMMUNICATION_ANALYSIS"
    DISCLOSE_TO_COUNSEL = "DISCLOSE_TO_COUNSEL"
    FILING_SUPPORT = "FILING_SUPPORT"
    DISCLOSE_TO_OPPOSING = "DISCLOSE_TO_OPPOSING"  # waiver-risk; privilege review

    # Legacy aliases (tests + older bridges)
    TENANCY = "TENANCY_RECORDS"
    TENANCY_FACTS = "TENANCY_RECORDS"
    MEDICAL = "MEDICAL_INFORMATION"
    FINANCIAL = "FINANCIAL_INFORMATION"
    PHOTOS = "PHOTOGRAPHS"
    AUDIO = "AUDIO_RECORDINGS"
    VIDEO = "VIDEO_RECORDINGS"
    AI_PROCESSING = "AI_ANALYSIS"
    CLOUD_PROCESSING = "CLOUD_STORAGE_IMPORT"
    THIRD_PARTY_COMMS = "CLIENT_COMMUNICATION_ANALYSIS"


class ConsentStatus(str, Enum):
    DRAFT = "DRAFT"
    PRESENTED = "PRESENTED"
    GRANTED = "GRANTED"
    ACTIVE = "ACTIVE"
    MODIFIED = "MODIFIED"
    WITHDRAWAL_REQUESTED = "WITHDRAWAL_REQUESTED"
    RESTRICTED = "RESTRICTED"
    WITHDRAWN = "WITHDRAWN"
    EXPIRED = "EXPIRED"
    DECLINED = "DECLINED"
    LEGAL_BASIS_REVIEW = "LEGAL_BASIS_REVIEW"
    PROCESSING_PERMITTED_WITHOUT_CONSENT = "PROCESSING_PERMITTED_WITHOUT_CONSENT"


PLAIN_LANGUAGE: dict[str, str] = {
    ConsentScope.MEDICAL_INFORMATION.value: (
        "Medical-record analysis: lets the system read medical documents you choose "
        "for this matter and identify dates or information potentially relevant to your case. "
        "It does not authorize disclosure to the other party or the public."
    ),
    ConsentScope.AI_ANALYSIS.value: (
        "AI analysis: allows private tools to organize and draft materials for lawyer review. "
        "It is not legal advice from a machine and does not waive privilege."
    ),
    ConsentScope.EXTERNAL_MODEL_PROCESSING.value: (
        "External model processing: sends approved, scoped material to a third-party model. "
        "Requires separate disclosure; never use for confidential files on a public Space."
    ),
    ConsentScope.PHOTOGRAPHS.value: (
        "Photographs: process photos you upload (e.g. unit condition). Originals are stored; "
        "not published."
    ),
    ConsentScope.TENANCY_RECORDS.value: (
        "Tenancy records: lease, notices, RTB materials for this matter only."
    ),
    ConsentScope.DISCLOSE_TO_OPPOSING.value: (
        "Disclosure to opposing party: high risk of privilege waiver. Requires privilege review "
        "and lawyer approval — not ordinary AI consent."
    ),
    ConsentScope.FINANCIAL_INFORMATION.value: (
        "Financial information: receipts, bank statements, rent ledgers for this matter."
    ),
    ConsentScope.AUDIO_RECORDINGS.value: (
        "Audio: hearing or other recordings. Transcription requires human verification before filing quotes."
    ),
}


def plain_language_for(scope: ConsentScope | str) -> str:
    key = scope.value if isinstance(scope, ConsentScope) else str(scope)
    # resolve aliases to canonical value
    try:
        key = ConsentScope(key).value
    except ValueError:
        pass
    return PLAIN_LANGUAGE.get(
        key,
        f"You authorize processing for category {key} for the stated purpose only. "
        "This is not a privilege waiver.",
    )


# Category used when mapping SourceType / privilege
TENANCY_FACTS = ConsentScope.TENANCY_RECORDS
