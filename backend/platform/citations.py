"""Citation verification (M3 foundation) — fail-closed registry lookup."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

from backend.db import get_connection, init_db

# Known official seeds (not full law text)
_OFFICIAL_PINS = {
    "rta": {
        "act": "Residential Tenancy Act",
        "source_id": "source_bc_laws",
        "url": "https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/02078_01",
    },
    "jrpa": {
        "act": "Judicial Review Procedure Act",
        "source_id": "source_bc_laws",
        "url": "https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/96241_01",
    },
    "ata": {
        "act": "Administrative Tribunals Act",
        "source_id": "source_bc_laws",
        "url": "https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/04045_01",
    },
}


def verify_citation(
    citation_text: str,
    *,
    matter_id: str = "",
    expected_topic: str = "",
) -> dict[str, Any]:
    """
    Fail-closed citation check.
    REJECTED if s.56 + retaliation topic; otherwise provisional VERIFIED_OFFICIAL_LINK only
    when act keywords match known registry (pinpoint still requires human/BC Laws).
    """
    text = (citation_text or "").strip()
    low = text.lower()
    reasons: list[str] = []
    status = "UNVERIFIED"
    source_id = None
    url = ""

    if not text:
        status = "REJECTED"
        reasons.append("Empty citation")
    elif re.search(r"s\.?\s*56\b", low) and "retaliat" in (expected_topic.lower() + low):
        status = "REJECTED"
        reasons.append(
            "RTA s.56 is not accepted as a retaliatory-eviction civil test "
            "(section-topic mismatch). Confirm heading on BC Laws."
        )
        source_id = "source_bc_laws"
    else:
        for key, meta in _OFFICIAL_PINS.items():
            if key in low or meta["act"].lower() in low:
                status = "PROVISIONAL"
                source_id = meta["source_id"]
                url = meta["url"]
                reasons.append(
                    f"Matched known official source registry for {meta['act']}. "
                    "Pinpoint and quotation must still be verified on BC Laws before court-ready use."
                )
                break
        if status == "UNVERIFIED":
            reasons.append(
                "No registry match. Do not treat as verified authority. "
                "Retrieve and hash-verify from official source."
            )

    vid = f"cit_{uuid.uuid4().hex[:12]}"
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO citation_verifications
            (verification_id, matter_id, citation_text, status, source_id, reasons)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (vid, matter_id, text, status, source_id, json.dumps(reasons)),
        )
    return {
        "verification_id": vid,
        "citation_text": text,
        "status": status,
        "source_id": source_id,
        "source_url": url,
        "reasons": reasons,
        "court_ready": False,  # never auto court-ready
    }


def list_knowledge_sources() -> list[dict[str, Any]]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT source_id, name, authority_type, jurisdiction, health_status FROM knowledge_sources"
        ).fetchall()
    return [dict(r) for r in rows]
