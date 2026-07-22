---
title: BC Legal AI Associate
emoji: ⚖️
colorFrom: blue
colorTo: gray
sdk: gradio
pinned: false
license: mit
---

# BC Legal AI Associate

Public Gradio demo for the BC Legal AI Associate project.

**Not a lawyer. Not legal advice.** Do not upload confidential client files here. The public Space runs in `APP_MODE=public_demo`, uses synthetic/demo inputs only, and keeps all outputs non-court-ready.

- **GitHub:** https://github.com/dmang69/bc-legal-ai  
- **Dataset:** https://huggingface.co/datasets/Dmang69/bc-legal-ai  
- **BC Laws:** https://www.bclaws.gov.bc.ca/  

The Space exposes deterministic safety/triage tools by default. Optional Transformers inference is disabled unless explicitly enabled through private Space secrets and safety gates. If enabling inference, set `HF_MODEL_ID` to a real Transformers-compatible base or adapter repo; do not point it at this policy/model-card/demo asset repo.

Private product delivery: Tauri 2 Workbench / Client / Portal against a private backend (see repo `docs/SECTION_G_PLATFORM_AND_DISTRIBUTION.md`).
