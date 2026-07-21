---
title: BC Legal AI Workbench
emoji: ⚖️
colorFrom: blue
colorTo: gray
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# BC Legal AI Workbench — Demo

Legal research, evidence analysis, and drafting **support** for British Columbia
civil and administrative work (RTB pathways, judicial review, superior court practice).

**Not a lawyer. Not legal advice.** No solicitor–client relationship is created.
Do not upload confidential client or litigation files to this public Space.
Verify all legislation on the official **BC Laws** portal before filing or reliance.

## What this demo shows

- **Matter triage** — notice-type deadline flags, forum routing (RTB / JR / BCHRT / MHPTA / strata),
  and the ASSUMPTIONS-requiring-verification discipline.
- **Analytical tagger** — decomposes draft text into FACT / ALLEGATION / LEGAL ARGUMENT /
  INFERENCE / ASSUMPTION / RECOMMENDATION candidates.
- **Official legislation links** — BC Laws only for statute text; CanLII for decisions only.
- **RTA pin self-check** — corrected section map per the repo verification log
  (BC Laws, current to July 14, 2026, accessed 2026-07-21).

## Design posture

RAG-first, LoRA-second. This Space performs **no model inference** and quotes **no
statute text from weights** — statute truth lives at BC Laws, retrieved and verified.
See `model/BASE_MODEL_DECISION.md` in the source repository.

Source: https://github.com/dmang69/bc-legal-ai
