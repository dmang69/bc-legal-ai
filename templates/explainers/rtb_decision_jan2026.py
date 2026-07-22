"""
SYNTHETIC plain-language explainer template for a fictional RTB decision.

No live court file numbers. Placeholders for demo training only.
"""

from __future__ import annotations

from architecture.document_explainer import DocumentExplainer


def rtb_decision_jan2026_explainer(
    *,
    matter_id: str | None = "DEMO-JR-0001",
    effective_eviction_date: str | None = None,
    vacate_by_date: str | None = None,
    key_findings: list[str] | None = None,
) -> DocumentExplainer:
    eff = effective_eviction_date or "[SYNTHETIC date — fill from decision]"
    vacate = vacate_by_date or "[SYNTHETIC date — fill from decision]"

    findings = key_findings or [
        "[SYNTHETIC] Summarized finding placeholder",
        "[SYNTHETIC] Planning theme: service-call volume treated as relevant (confirm decision text)",
    ]

    return DocumentExplainer(
        explainer_id="EXP-RTB-DEC-DEMO-001",
        document_title="[SYNTHETIC] RTB Decision",
        document_date="[SYNTHETIC] January 15, 2026",
        document_revision="[SYNTHETIC] REV placeholder",
        matter_id=matter_id,
        evidence_node_id=None,
        what_this_says=[
            "[SYNTHETIC] The arbitrator decided the landlord's eviction notice is valid",
            f"[SYNTHETIC] The effective date of eviction is {eff}",
            f"[SYNTHETIC] You are ordered to vacate by {vacate}",
        ],
        what_this_means=[
            f"[SYNTHETIC] Demo only — leave by {vacate} unless petition + stay (real matters: counsel)",
            "A petition alone may not stop the eviction timeline — a stay is a separate court order (confirm with counsel).",
            "Workbench file label: DEMO-JR-0001 (synthetic — not a real registry number).",
        ],
        key_findings=findings,
        possible_errors=[
            '[SYNTHETIC] Example theme: accepted high volume of police calls without breakdown of outcomes',
            "[SYNTHETIC] Example theme: procedural fairness / opportunity to respond",
        ],
        options=[
            "[SYNTHETIC] Discuss judicial review (Form 66 petition) with counsel",
            "[SYNTHETIC] Discuss stay application (typically Form 32) with counsel",
            "[SYNTHETIC] Confirm limitation using deadline engine (60 days from issuance — ATA s.57; extension is counsel-driven)",
        ],
        placeholders_remaining=[
            "effective_eviction_date",
            "vacate_by_date",
        ]
        if effective_eviction_date is None
        else [],
        disclaimer=(
            "This explanation is not legal advice. SYNTHETIC DEMO ONLY. "
            "It is a plain-language summary template for discussion with a lawyer."
        ),
    )
