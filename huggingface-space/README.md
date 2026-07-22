---
title: BC Legal AI Associate
emoji: ⚖️
colorFrom: blue
colorTo: gray
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# BC Legal AI Associate — Public Demo

Legal research, evidence analysis, and drafting **support** for British Columbia
civil and administrative work (RTB pathways, judicial review, superior court practice).

**Not a lawyer. Not legal advice.** No solicitor–client relationship is created.
Do not upload confidential client or litigation files to this public Space.
Runs with `APP_MODE=public_demo` (synthetic scenarios only).

Verify all legislation on the official **BC Laws** portal before filing or reliance.

## What this demo shows

- **Matter triage** — notice-type deadline flags, forum routing (RTB / JR / BCHRT / MHPTA / strata),
  and the ASSUMPTIONS-requiring-verification discipline.
- **Analytical tagger** — decomposes draft text into FACT / ALLEGATION / LEGAL ARGUMENT /
  INFERENCE / ASSUMPTION / RECOMMENDATION candidates.
- **Official legislation links** — BC Laws only for statute text; CanLII for decisions only.
- **Synthetic JR / post-resolution demos** — no live matter data.

## Full product (not this Space)

Private backend + **Tauri 2** clients (Workbench / Client / Portal): see Section G in the repo.

- GitHub: https://github.com/dmang69/bc-legal-ai
- Install strategy: `docs/SECTION_G_PLATFORM_AND_DISTRIBUTION.md`

## Design posture

RAG-first, LoRA-second. This Space performs **no model inference** and quotes **no
statute text from weights** — statute truth lives at BC Laws, retrieved and verified.

