"""Citation verification (M3 foundation) — fail-closed registry lookup.

IMPORTANT: This is NOT full citation verification. It performs keyword matching
against three known statute identifiers and returns a source URL. It does NOT:
- Retrieve the cited section text
- Validate quotation or paraphrase alignment
- Establish a pinpoint span
- Determine currency or version of the law
- Check case treatment or binding weight

The `court_ready` field is always False. This function should not be described
as full citation verification.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from backend.db import get_connection, init_db

@dataclass(frozen=True)
class SourceModel:
    source_id: str
    name: str
    authority_type: str
    jurisdiction: str
    url: str
    retrieval_method: str = "official_registry_seed"
    health_status: str = "MANUAL_VERIFICATION_REQUIRED"


@dataclass(frozen=True)
class CitationAuditRecord:
    verification_id: str
    citation_text: str
    status: str
    source_id: str | None
    source_url: str
    authority_type: str
    jurisdiction: str
    expected_topic: str
    source_hash: str
    currency_date: str
    reasons: list[str]
    court_ready: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Known official seeds (not full law text)
_OFFICIAL_PINS = {
    "rta": {
        "act": "Residential Tenancy Act",
        "source_id": "source_bc_laws",
        "url": "https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/02078_01",
        "authority_type": "STATUTE",
        "jurisdiction": "BC",
        "currency_date": "manual_recheck_required",
    },
    "jrpa": {
        "act": "Judicial Review Procedure Act",
        "source_id": "source_bc_laws",
        "url": "https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/96241_01",
        "authority_type": "STATUTE",
        "jurisdiction": "BC",
        "currency_date": "manual_recheck_required",
    },
    "ata": {
        "act": "Administrative Tribunals Act",
        "source_id": "source_bc_laws",
        "url": "https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/04045_01",
        "authority_type": "STATUTE",
        "jurisdiction": "BC",
        "currency_date": "manual_recheck_required",
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

    Returns KEYWORD_MATCH_ONLY when act keywords match known registry.
    Returns REJECTED for known incorrect mappings (e.g., s.56 + retaliation).
    Returns UNVERIFIED for unrecognized citations.

    This is NOT full citation verification. Section retrieval, pinpoint,
    quotation verification, and currency checking are NOT implemented.
    court_ready is always False.
    """
    text = (citation_text or "").strip()
    low = text.lower()
    reasons: list[str] = []
    status = "UNVERIFIED"
    source_id = None
    url = ""
    authority_type = "UNKNOWN"
    jurisdiction = ""
    currency_date = ""

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
        url = _OFFICIAL_PINS["rta"]["url"]
        authority_type = _OFFICIAL_PINS["rta"]["authority_type"]
        jurisdiction = _OFFICIAL_PINS["rta"]["jurisdiction"]
        currency_date = _OFFICIAL_PINS["rta"]["currency_date"]
    else:
        for key, meta in _OFFICIAL_PINS.items():
            if key in low or meta["act"].lower() in low:
                status = "KEYWORD_MATCH_ONLY"
                source_id = meta["source_id"]
                url = meta["url"]
                authority_type = meta["authority_type"]
                jurisdiction = meta["jurisdiction"]
                currency_date = meta["currency_date"]
                reasons.append(
                    f"Keyword match against official source registry for {meta['act']}. "
                    "This is NOT full citation verification. Section retrieval, pinpoint validation, "
                    "quotation verification, and currency checking are NOT yet implemented. "
                    "Must verify on BC Laws before any court-ready use."
                )
                break
        if status == "UNVERIFIED":
            reasons.append(
                "No registry match. Do not treat as verified authority. "
                "Retrieve and hash-verify from official source."
            )

    vid = f"cit_{uuid.uuid4().hex[:12]}"
    source_hash = hashlib.sha256(f"{source_id or ''}|{url}|{text}".encode("utf-8")).hexdigest() if source_id else ""
    record = CitationAuditRecord(
        verification_id=vid,
        citation_text=text,
        status=status,
        source_id=source_id,
        source_url=url,
        authority_type=authority_type,
        jurisdiction=jurisdiction,
        expected_topic=expected_topic,
        source_hash=source_hash,
        currency_date=currency_date,
        reasons=reasons,
        court_ready=False,
    )
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO citation_verifications
            (verification_id, matter_id, citation_text, status, source_id, source_url,
             authority_type, jurisdiction, expected_topic, source_hash, currency_date,
             reasons, court_ready)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vid,
                matter_id,
                text,
                status,
                source_id,
                url,
                authority_type,
                jurisdiction,
                expected_topic,
                source_hash,
                currency_date,
                json.dumps(reasons),
                0,
            ),
        )
        conn.execute(
            """
            INSERT INTO citation_audit_events
            (audit_id, verification_id, matter_id, event_type, detail_json)
            VALUES (?, ?, ?, 'citation.verify', ?)
            """,
            (f"caud_{uuid.uuid4().hex[:12]}", vid, matter_id, json.dumps(record.to_dict())),
        )
    return record.to_dict()


def list_knowledge_sources() -> list[dict[str, Any]]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT source_id, name, authority_type, jurisdiction, permitted_content,
                   retrieval_method, health_status, terms_reviewed_at, last_successful_update
            FROM knowledge_sources
            """
        ).fetchall()
    return [dict(r) for r in rows]


def list_citation_audit(matter_id: str = "") -> list[dict[str, Any]]:
    init_db()
    sql = """
        SELECT verification_id, matter_id, citation_text, status, source_id, source_url,
               authority_type, jurisdiction, expected_topic, source_hash, currency_date,
               reasons, court_ready, created_at
        FROM citation_verifications
    """
    params: tuple[Any, ...] = ()
    if matter_id:
        sql += " WHERE matter_id = ?"
        params = (matter_id,)
    sql += " ORDER BY created_at DESC"
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["reasons"] = json.loads(item.get("reasons") or "[]")
        item["court_ready"] = bool(item.get("court_ready"))
        out.append(item)
    return out
