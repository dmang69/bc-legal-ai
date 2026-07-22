"""Drafting scaffolds (M5 start) — Form 66/67 outlines; not court-ready without gates."""

from __future__ import annotations

from typing import Any

from backend.identity import AuthError, UserInfo, get_identity_service


def petition_outline(user: UserInfo, matter_id: str) -> dict[str, Any]:
    if not get_identity_service().can_access_matter(user, matter_id):
        raise AuthError("Matter access denied")
    try:
        from templates.petition.rtb_jr_petition_outline import rtb_jr_petition_outline

        outline = rtb_jr_petition_outline(matter_id=matter_id)
        payload = outline.to_dict() if hasattr(outline, "to_dict") else {"raw": str(outline)}
    except Exception as e:
        payload = {
            "form_number": "66",
            "document_type": "PETITION",
            "title": "Petition scaffold (Form 66)",
            "error": str(e),
            "sections": [
                "Style of cause (synthetic parties only in public demos)",
                "Orders sought",
                "Grounds (patent unreasonableness / procedural fairness — confirm counsel)",
                "Material facts (source-linked only)",
                "Legal basis (verified authorities only)",
            ],
        }
    payload["court_ready"] = False
    payload["requires"] = [
        "privilege review",
        "citation verification",
        "HUMAN_CONFIRMED facts",
        "supervising lawyer approval",
    ]
    payload["form_number"] = payload.get("form_number") or "66"
    return payload


def response_outline(user: UserInfo, matter_id: str) -> dict[str, Any]:
    if not get_identity_service().can_access_matter(user, matter_id):
        raise AuthError("Matter access denied")
    return {
        "form_number": "67",
        "document_type": "RESPONSE_TO_PETITION",
        "title": "Response to Petition scaffold (Form 67)",
        "court_ready": False,
        "sections": [
            "Response to orders sought",
            "Response to grounds",
            "Additional material facts",
            "Legal basis",
        ],
        "requires": [
            "privilege review",
            "citation verification",
            "supervising lawyer approval",
        ],
    }
