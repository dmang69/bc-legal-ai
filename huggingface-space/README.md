---
title: BC Legal AI Associate
emoji: ⚖️
colorFrom: blue
colorTo: gray
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
pinned: false
license: mit
---

# BC Legal AI Associate

Public deterministic Gradio demonstration for the BC Legal AI Associate project. Model inference is disabled by default; the public Space performs rule-based synthetic triage and links to official sources.

**Not a lawyer. Not legal advice.** Do not upload confidential client files here.

- **GitHub:** https://github.com/dmang69/bc-legal-ai  
- **Dataset:** https://huggingface.co/datasets/Dmang69/bc-legal-ai  
- **Model documentation:** https://huggingface.co/Dmang69/bc-legal-ai-base  
- **BC Laws:** https://www.bclaws.gov.bc.ca/  

The linked model repository must not be loaded as a Transformers checkpoint unless it contains a complete standard configuration, tokenizer, and compatible weights. A policy card is not a model architecture. Optional private inference requires `ENABLE_TRANSFORMERS_INFERENCE=true`, a reviewed standard `HF_MODEL_ID`, and an immutable commit SHA in `HF_MODEL_REVISION`; remote repository code is blocked.

The public deployment uses the Gradio SDK and remains synthetic-only. It must not accept confidential files or represent outputs as legal advice or court-ready work.

Private product delivery: Tauri 2 Workbench / Client / Portal against a private backend (see repo `docs/SECTION_G_PLATFORM_AND_DISTRIBUTION.md`).
