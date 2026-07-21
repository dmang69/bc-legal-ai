"""
Plain-language explainer: RTB Decision dated January 15, 2026 (REV January 20).

Tied to JR file KAM-S-S-65285 / petition PET-JR-RTB-001 analysis themes.
Fill placeholders when the written decision is received (dashboard: awaiting from RTB).
"""

from __future__ import annotations

from architecture.document_explainer import DocumentExplainer


def rtb_decision_jan2026_explainer(
    *,
    matter_id: str | None = "KAM-S-S-65285",
    effective_eviction_date: str | None = None,
    vacate_by_date: str | None = None,
    key_findings: list[str] | None = None,
) -> DocumentExplainer:
    """
    Template + case-linked error themes from petition outline.

    effective_eviction_date / vacate_by_date: fill from written decision when available.
    """
    eff = effective_eviction_date or "[date — fill from written RTB decision]"
    vacate = vacate_by_date or "[date — fill from written RTB decision]"

    findings = key_findings or [
        "[Summarized in plain language once written decision is on file]",
        "Planning theme: arbitrator treated high volume of police calls as supporting "
        "concern about illegal activity / nuisance (confirm exact wording in decision).",
        "Planning theme: landlord’s eviction notice treated as valid (confirm grounds cited).",
    ]

    return DocumentExplainer(
        explainer_id="EXP-RTB-DEC-2026-01-15",
        document_title="RTB Decision",
        document_date="January 15, 2026",
        document_revision="REV January 20",
        matter_id=matter_id,
        evidence_node_id=None,  # set when PDF uploaded to matrix
        what_this_says=[
            "The arbitrator decided your landlord's eviction notice is valid",
            f"The effective date of eviction is {eff}",
            f"You are ordered to vacate by {vacate}",
        ],
        what_this_means=[
            f"You must leave the unit by {vacate} unless both of the following happen:",
            "  1. You file a judicial review petition with BC Supreme Court, AND",
            "  2. You get a stay of the order from the court",
            "A petition alone may not stop the eviction timeline — a stay is a separate "
            "court order (confirm procedure with counsel).",
            "Court file reference in workbench: KAM-S-S-65285 (confirm registry details).",
        ],
        key_findings=findings,
        possible_errors=[
            # From petition outline Layer 3 / Ground 1–2 themes — not final legal conclusions
            'Accepted "400 police calls" as supporting illegal activity without requiring '
            "a breakdown of call outcomes (see EM-031 / transcript 25:40–26:40 themes)",
            "Did not clearly distinguish calls for service from confirmed illegal activity "
            "(petition Ground 1b — verify RTA s. 47 fit on BC Laws)",
            'Accepted "nuisance property" designation without documentary proof '
            "(transcript 37:00 theme)",
            "Procedural fairness concerns: SRL service guidance and exclusion of "
            "mayor/bylaw emails without clear explanation (Ground 2 themes — verify transcript)",
            "Full error list requires the written reasons; update when RTB decision PDF is received",
        ],
        options=[
            "File judicial review (planning deadline in dashboard: March 21, 2026 — "
            "CONFIRM limitation under JRPA / applicable rules before relying)",
            "Apply for a stay of eviction (separate from filing the petition)",
            "Negotiate move-out date with landlord",
            "Seek legal assistance (resources listed below)",
        ],
        resources=[
            "Access Pro Bono / lawyer referral — https://www.accessprobono.ca/ (verify current links)",
            "Legal Aid BC — https://legalaid.bc.ca/ (eligibility rules apply)",
            "BC Supreme Court self-help / registry information — courts.gov.bc.ca (verify)",
            "RTB: request written decision / recording if not yet received",
            "Independent counsel strongly recommended for JR + stay strategy",
        ],
        placeholders_remaining=[
            "effective_eviction_date",
            "vacate_by_date",
            "key_findings (plain-language summary of written reasons)",
            "Upload written RTB decision + hearing audio to Evidence Matrix",
        ],
    )
