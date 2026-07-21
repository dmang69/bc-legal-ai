"""
BC Legal AI Associate — public demo Space (CPU-only, no model weights).

Design posture (per model/BASE_MODEL_DECISION.md, 2026-07-21):
- RAG-first, LoRA-second. Statute truth comes from BC Laws, never from memory.
- This demo performs NO inference and quotes NO statute text from weights.
- It demonstrates: matter triage, deadline flags, analytical tagging, and
  fail-closed routing to official sources.

Not a lawyer. Not legal advice. Legal information and drafting support only.
"""

from __future__ import annotations

import re

import gradio as gr

DISCLAIMER = """
**Disclaimer:** **BC Legal AI Associate** — legal research and drafting **support** only.
This is **not** a licensed lawyer, **not legal advice**, and does not create a
solicitor–client relationship. Do **not** upload confidential client or litigation
files to this public Space. Verify all legislation on the official **BC Laws**
portal before filing or reliance. Court-ready work requires a licensed supervising
lawyer and human approval.
"""

FAIL_CLOSED = (
    "> **Fail-closed note:** this demo does not retrieve live law. Every section "
    "reference below must be re-verified on **BC Laws** (check the 'current to' "
    "line) before any reliance or filing."
)

OFFICIAL_LAWS = [
    (
        "Residential Tenancy Act, SBC 2002, c 78",
        "https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/02078_01",
        "Primary residential tenancy statute (BC Laws only).",
    ),
    (
        "Judicial Review Procedure Act, RSBC 1996, c 241",
        "https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/96241_01",
        "Judicial review applications in BC Supreme Court.",
    ),
    (
        "Manufactured Home Park Tenancy Act, SBC 2002, c 77",
        "https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/02077_01",
        "Pad tenancies / manufactured home parks.",
    ),
    (
        "BC Laws portal (home)",
        "https://www.bclaws.gov.bc.ca/",
        "Search all official BC enactments. Currency lines on each Act.",
    ),
    (
        "Residential Tenancy Branch (government)",
        "https://www2.gov.bc.ca/gov/content/housing-tenancy/residential-tenancies",
        "Forms, fees, policy guidelines — verify before filing.",
    ),
    (
        "CanLII (BC decisions)",
        "https://www.canlii.org/en/bc/",
        "RTB decisions (published subset) and BCSC/BCCA judicial review jurisprudence. Cases only — never statute text.",
    ),
    (
        "BC Human Rights Tribunal",
        "https://www.bchrt.bc.ca/",
        "Discrimination complaints (not a source for RTA text).",
    ),
]

# Section map transcribed from the repo verification log
# (legislation/court-ready, verified against BC Laws 2026-07-21,
# consolidation "current to July 14, 2026"). Re-verify before filing.
RTA_VERIFIED_MAP = """
### Residential Tenancy Act — verified section map (re-check before filing)

| Topic | Official section (BC Laws) |
|-------|----------------------------|
| Cannot contract out of Act | **s. 5** |
| Enforce rights between landlord & tenant | **s. 6** |
| Application / processing fees prohibited | **s. 15** |
| Deposit maximums (½ month each) | **s. 19** |
| Deposit prohibitions | **s. 20** |
| Acceleration term prohibited | **s. 22** |
| Quiet enjoyment | **s. 28** |
| Entry (24h notice; 8 a.m.–9 p.m.) | **s. 29** |
| Repair and maintain | **s. 32** |
| Emergency repairs | **s. 33** |
| Deposit return / double amount | **s. 38** |
| Rent increase timing | **s. 42** |
| Rent increase amount | **s. 43** |

**Source:** BC Laws RTA HTML consolidation, per repo verification log.
**Currency line recorded:** current to **July 14, 2026** · **Accessed:** 2026-07-21.
**Do not** print statute text from CanLII for court packages.
"""

# ---------------------------------------------------------------------------
# Matter triage (rule-based demonstration of the orchestration layer)
# ---------------------------------------------------------------------------

NOTICE_RULES = [
    {
        "patterns": [r"\bten[\s-]?day\b", r"\b10[\s-]?day\b", r"\bnon[\s-]?payment\b"],
        "label": "Ten Day Notice (unpaid rent/utilities)",
        "window": "**5 days** from service to pay in full **or** file a dispute (RTB).",
    },
    {
        "patterns": [r"\bone[\s-]?month\b", r"\b1[\s-]?month\b", r"\bfor cause\b"],
        "label": "One Month Notice (cause)",
        "window": "**10 days** from service to file a dispute.",
    },
    {
        "patterns": [r"\btwo[\s-]?month\b", r"\b2[\s-]?month\b", r"\blandlord'?s use\b"],
        "label": "Two Month Notice (landlord's use of property)",
        "window": "**15 days** from service to file a dispute.",
    },
    {
        "patterns": [r"\bfour[\s-]?month\b", r"\b4[\s-]?month\b", r"\brenoviction\b",
                     r"\bdemolition\b", r"\brenovation\b", r"\bconversion\b"],
        "label": "Four Month Notice (demolition / renovation / conversion)",
        "window": "**15 days** from service to file a dispute. Renovation-based notices engage a tenant right of first refusal — verify current RTA text on BC Laws.",
    },
]

FORUM_RULES = [
    {
        "patterns": [r"\bjudicial review\b", r"\border of possession\b", r"\bstay\b",
                     r"\bunreasonable\b", r"\bprocedural fairness\b", r"\bpatently\b",
                     r"\bvavilov\b", r"\bjrpa\b", r"\bpetition\b"],
        "forum": "BC Supreme Court — Judicial Review (JRPA petition)",
        "note": "Tight timelines; grounds limited to reasonableness / fairness / jurisdiction. Stay applications engage the three-part test. Flag: **[INDEPENDENT COUNSEL RECOMMENDED]**.",
    },
    {
        "patterns": [r"\bdiscriminat", r"\bservice animal\b", r"\bdisabilit",
                     r"\bfamily status\b", r"\bsource of income\b", r"\bharass"],
        "forum": "BC Human Rights Tribunal (possible dual filing with RTB)",
        "note": "One-year filing window from the last alleged discriminatory act. RTB and BCHRT remedies are complementary.",
    },
    {
        "patterns": [r"\bmanufactured home\b", r"\bmobile home\b", r"\bpark pad\b", r"\bmhpta\b"],
        "forum": "RTB under the Manufactured Home Park Tenancy Act",
        "note": "Pad tenancies follow a parallel framework with materially longer notice periods. Verify on BC Laws.",
    },
    {
        "patterns": [r"\bstrata\b", r"\bcondo\b", r"\bbylaw fine\b"],
        "forum": "RTB (tenancy) with Strata Property Act overlay",
        "note": "Strata obligations generally bind the owner, not the tenant; passing fines through may offend the RTA. Verify current RTA text.",
    },
    {
        "patterns": [r"\brent\b", r"\bevict", r"\bnotice\b", r"\bdeposit\b", r"\brepairs?\b",
                     r"\bmold\b", r"\bmould\b", r"\blandlord\b", r"\btenant\b", r"\blease\b",
                     r"\btenancy\b", r"\bentry\b"],
        "forum": "Residential Tenancy Branch (RTB) — Residential Tenancy Act",
        "note": "Standard RTB dispute resolution path. Evidence deadline is typically 14 days before hearing — confirm with the RTB.",
    },
]


def triage(scenario: str) -> str:
    if not scenario or not scenario.strip():
        return "Describe the situation above (facts only — no names or confidential details)."

    text = scenario.lower()
    out = ["## Triage result (demonstration output — not legal advice)", ""]

    out.append("### PROCEDURAL FLAGS")
    hits = [r for r in NOTICE_RULES if any(re.search(p, text) for p in r["patterns"])]
    if hits:
        for h in hits:
            out.append(f"- **{h['label']}** — dispute window: {h['window']}")
        out.append("- Deadlines run from the **date of service**; deemed-service rules can add days for mailed notices. Calendar the deadline **today**.")
    else:
        out.append("- No standard notice type detected. If any notice was served, identify its form and service date before anything else.")
    out.append("")

    out.append("### FORUM ROUTING")
    forums = [f for f in FORUM_RULES if any(re.search(p, text) for p in f["patterns"])]
    seen = set()
    for f in forums:
        if f["forum"] in seen:
            continue
        seen.add(f["forum"])
        out.append(f"- **{f['forum']}** — {f['note']}")
    if not seen:
        out.append("- No forum matched. More facts needed.")
    out.append("")

    out.append("### ANALYTICAL DISCIPLINE (apply to every work product)")
    out.append("Separate and label: **FACT · ALLEGATION · LEGAL ARGUMENT · INFERENCE · ASSUMPTION · PROCEDURAL HISTORY · RECOMMENDATION**.")
    out.append("")
    out.append("### ASSUMPTIONS REQUIRING VERIFICATION")
    out.append("- Current statute text and section numbering on BC Laws (check the 'current to' line).")
    out.append("- Whether the event date requires a **historical / point-in-time** version of the Act.")
    out.append("- Service method and date for any notice (drives every deadline).")
    out.append("")
    out.append(FAIL_CLOSED)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Analytical tagger (demonstration of the FACT/ALLEGATION/... discipline)
# ---------------------------------------------------------------------------

TAG_RULES = [
    ("ASSUMPTION", [r"\bi (think|believe|assume|guess)\b", r"\bprobably\b", r"\bmaybe\b", r"\bmust have\b"]),
    ("ALLEGATION", [r"\balleg", r"\bclaims?\b", r"\baccus", r"\bhe said\b", r"\bshe said\b", r"\bthey said\b"]),
    ("RECOMMENDATION", [r"\bshould\b", r"\brecommend", r"\bnext step\b", r"\bi advise\b"]),
    ("LEGAL ARGUMENT", [r"\bs\.\s?\d", r"\bsection \d", r"\bact\b", r"\bcharter\b", r"\bprecedent\b", r"\bvavilov\b"]),
    ("FACT (candidate — needs exhibit)", [r"\b\d{4}-\d{2}-\d{2}\b", r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b", r"\$\s?\d", r"\bexhibit\b", r"\breceipt\b", r"\be-?transfer\b"]),
]


def tag_text(raw: str) -> str:
    if not raw or not raw.strip():
        return "Paste a paragraph above to see it decomposed into analytical tags."
    # Protect periods inside common legal abbreviations (s. 28, e.g., v., c.)
    # so the sentence splitter does not fragment citations.
    protected = re.sub(r"\b(s|e\.g|i\.e|No|Nos|vs|v|c|paras?)\.", r"\1∯", raw.strip())
    sentences = [
        s.replace("∯", ".").strip()
        for s in re.split(r"(?<=[.!?])\s+", protected)
        if s.strip()
    ]
    lines = ["## Tagged decomposition (heuristic demo — human review required)", ""]
    for i, s in enumerate(sentences, 1):
        low = s.lower()
        tag = "UNCLASSIFIED"
        for name, pats in TAG_RULES:
            if any(re.search(p, low) for p in pats):
                tag = name
                break
        lines.append(f"{i}. **[{tag}]** {s}")
    lines.append("")
    lines.append("> Candidates tagged FACT still require an exhibit or document anchor before they may be relied on as established fact.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# RTA pin self-check (corrected pins — see RTA_VERIFIED_MAP)
# ---------------------------------------------------------------------------

def quiz_section(choice: str) -> str:
    answers = {
        "Cannot contract out of RTA": (
            "Official answer: **s. 5** (not s. 6).\n\n"
            "s. 6 is about enforcing rights between landlord and tenant.\n"
            "Verify: BC Laws RTA link above."
        ),
        "Quiet enjoyment": (
            "Official answer: **s. 28** (not s. 22).\n\n"
            "s. 22 prohibits acceleration terms.\n"
            "Verify: BC Laws RTA link above."
        ),
        "Landlord entry notice": (
            "Official answer: **s. 29** — at least 24 hours written notice; "
            "entry between **8 a.m. and 9 p.m.** unless tenant agrees "
            "(plus other listed exceptions).\n"
            "Verify: BC Laws RTA link above."
        ),
        "Deposit return timeline": (
            "Official answer: **s. 38** — generally within **15 days** after the later of "
            "tenancy end or written forwarding address; non-compliance can trigger "
            "**double** the deposit (s. 38(6)).\n"
            "Verify full section on BC Laws before filing."
        ),
    }
    return answers.get(choice, "Pick a topic.")


def laws_markdown() -> str:
    lines = ["### Official links (Government of BC / BC Laws / CanLII for cases only)", ""]
    for title, url, note in OFFICIAL_LAWS:
        lines.append(f"- **[{title}]({url})** — {note}")
    lines.append("")
    lines.append(RTA_VERIFIED_MAP)
    return "\n".join(lines)


with gr.Blocks(title="BC Legal AI Associate") as demo:
    gr.Markdown("# BC Legal AI Associate — Public Demo")
    gr.Markdown(DISCLAIMER)

    with gr.Tabs():
        with gr.Tab("Matter triage"):
            gr.Markdown(
                "Paste a **non-confidential** description of a tenancy or tribunal "
                "situation. The demo flags notice deadlines, routes the forum, and "
                "shows the analytical-tag discipline. No statute text is generated."
            )
            scenario = gr.Textbox(
                lines=6,
                label="Situation (facts only — no names, addresses, or confidential details)",
                placeholder="e.g. I received a two month notice for landlord's use on July 2, and the landlord previously raised my rent informally...",
            )
            triage_btn = gr.Button("Run triage", variant="primary")
            triage_out = gr.Markdown()
            triage_btn.click(triage, inputs=scenario, outputs=triage_out)

        with gr.Tab("Analytical tagger"):
            gr.Markdown(
                "Paste a draft paragraph. The demo decomposes it into "
                "**FACT / ALLEGATION / ASSUMPTION / LEGAL ARGUMENT / RECOMMENDATION** "
                "candidates for human review."
            )
            tag_in = gr.Textbox(lines=6, label="Draft text")
            tag_btn = gr.Button("Decompose", variant="primary")
            tag_out = gr.Markdown()
            tag_btn.click(tag_text, inputs=tag_in, outputs=tag_out)

        with gr.Tab("Official legislation"):
            gr.Markdown(laws_markdown())
            gr.Markdown(
                "For court Books of Authorities: **Print / Save PDF** from the BC Laws page "
                "on the day of filing; re-check the 'current to' line."
            )

        with gr.Tab("RTA pin self-check"):
            gr.Markdown(
                "Quick check of common **wrong-memory** pins. "
                "Always re-open BC Laws before a real filing."
            )
            topic = gr.Dropdown(
                [
                    "Cannot contract out of RTA",
                    "Quiet enjoyment",
                    "Landlord entry notice",
                    "Deposit return timeline",
                ],
                label="Topic",
                value="Cannot contract out of RTA",
            )
            quiz_out = gr.Markdown()
            topic.change(quiz_section, inputs=topic, outputs=quiz_out)
            demo.load(quiz_section, inputs=topic, outputs=quiz_out)

    gr.Markdown(
        "Source: [github.com/dmang69/bc-legal-ai](https://github.com/dmang69/bc-legal-ai) — "
        "skills, verification logs, and the base-model / fine-tuning designation."
    )


if __name__ == "__main__":
    demo.launch()
