"""
BC Legal AI — public index Space
Official legislation links point only to BC Laws (not CanLII for statutes).
Not legal advice.
"""

from __future__ import annotations

import gradio as gr

DISCLAIMER = """
**Disclaimer:** This Space provides **legal information and skill navigation only**.  
It is **not legal advice** and does not create a solicitor–client relationship.  
Verify all legislation on the official **BC Laws** portal before filing or reliance.
"""

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
        "BC Human Rights Tribunal",
        "https://www.bchrt.bc.ca/",
        "Discrimination complaints (not a source for RTA text).",
    ),
]

# Official RTA pins verified 2026-07-21 against BC Laws (current to 14 July 2026)
RTA_CORRECT_MAP = """
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

**Source:** BC Laws RTA HTML consolidation.  
**Currency line recorded:** current to **July 14, 2026** · **Accessed:** 2026-07-21.  
**Do not** print statute text from CanLII for court packages.
"""

SKILLS = """
### Skills in the BC Legal AI workbench

| Skill | Role |
|-------|------|
| supreme-court-civil-counsel | Superior court drafting standard (SRL-aware) |
| bc-tenancy-substantive | Deep RTA / bad-faith / eviction defence |
| bc-tenancy-procedure | Evidence, hearings, settlement, enforcement |
| bc-tenancy-advocacy / advanced | JR, human rights, strata, MHPTA |
| bc-judicial-review-guide | Petitions, stays, Vavilov framing |
| bc-legislation-admin | **BC Laws only** statutory retrieval |
| canlii-boa-builder | Cases for BOA (not statute text) |
| critical-reading | Decompose decisions & affidavits |
| cognitive-awareness | Calibration, failure modes, synthesis |
| self-improvement | Reactive skill patches |
| learning-mode | Tutoring pedagogy |
| doc-coauthoring | Collaborative doc workflow |
| legal-lexicon-cultivation | Glossary / dictionary discipline |

Full package: Hugging Face **dataset** `bc-legal-ai` and GitHub `bc-legal-ai`.
"""


def laws_markdown() -> str:
    lines = ["### Official links (Government of BC / BC Laws)", ""]
    for title, url, note in OFFICIAL_LAWS:
        lines.append(f"- **[{title}]({url})** — {note}")
    lines.append("")
    lines.append(RTA_CORRECT_MAP)
    return "\n".join(lines)


def quiz_section(choice: str) -> str:
    """Quick self-check (learning mode style, not a dump of wrong pins)."""
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


with gr.Blocks(title="BC Legal AI Workbench") as demo:
    gr.Markdown("# BC Legal AI Workbench")
    gr.Markdown(DISCLAIMER)

    with gr.Tabs():
        with gr.Tab("Official legislation"):
            gr.Markdown(laws_markdown())
            gr.Markdown(
                "For court Books of Authorities: **Print / Save PDF** from the BC Laws page "
                "on the day of filing; re-check the 'current to' line."
            )

        with gr.Tab("Skills index"):
            gr.Markdown(SKILLS)

        with gr.Tab("RTA pin self-check"):
            gr.Markdown(
                "Quick check of common **wrong memory** pins. "
                "Always re-open BC Laws before a real filing."
            )
            topic = gr.Dropdown(
                list(
                    [
                        "Cannot contract out of RTA",
                        "Quiet enjoyment",
                        "Landlord entry notice",
                        "Deposit return timeline",
                    ]
                ),
                label="Topic",
                value="Cannot contract out of RTA",
            )
            out = gr.Markdown()
            topic.change(quiz_section, inputs=topic, outputs=out)
            demo.load(quiz_section, inputs=topic, outputs=out)

    gr.Markdown(
        "Dataset + full skills: search Hugging Face for **bc-legal-ai**. "
        "GitHub: create/push `bc-legal-ai` with the publish scripts in the repo."
    )


if __name__ == "__main__":
    demo.launch()
