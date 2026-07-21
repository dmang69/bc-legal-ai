---
title: BC Legal AI Associate
emoji: ⚖️
colorFrom: indigo
colorTo: gray
sdk: gradio
sdk_version: 6.20.0
app_file: app.py
short_description: CPU demo — triage, tags, BC Laws routing (no model weights)
python_version: "3.12"
---

# BC Legal AI Associate — Public Demo

CPU-only Gradio Space. **No model weights. No LLM inference.**

Demonstrates:

- Matter triage (notice windows + forum routing)
- Analytical tag decomposition (FACT / ALLEGATION / …)
- Official BC Laws links + verified RTA section map
- RTA pin self-check (common wrong-memory corrections)

**Not a lawyer. Not legal advice.** Legal research and drafting **support** only.  
Do **not** upload confidential client or litigation files.

Statute truth: [BC Laws](https://www.bclaws.gov.bc.ca/) only (re-check “current to” before filing).  
Source monorepo: https://github.com/dmang69/bc-legal-ai
