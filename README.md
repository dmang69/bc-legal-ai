# BC Legal AI Associate

**Human-supervised** legal research, evidence, drafting, and matter-support platform for British Columbia.

**Not a lawyer. Not legal advice.** No solicitor–client relationship is created.

## Product description (target platform)

**[`docs/PRODUCT_DESCRIPTION.md`](docs/PRODUCT_DESCRIPTION.md)** — integrated supervised practice platform  

**[`docs/CONVERSATIONAL_WORKSPACE_SPEC.md`](docs/CONVERSATIONAL_WORKSPACE_SPEC.md)** — chat-first multi-agent workspace (primary UX)

The platform shell (web/desktop/mobile) is only the **container**. The product is a **conversational AI legal operating environment**: matter chats, research, drafting beside the conversation, specialist agents, evidence links, and human approvals — **not** autonomous legal practice.

## Current implementation status

Honest maturity and gaps: **[`PRODUCT_STATUS.md`](PRODUCT_STATUS.md)**  
Engineering roadmap: **[`docs/PHASE_4_MASTER_ENGINEERING_PROGRAM.md`](docs/PHASE_4_MASTER_ENGINEERING_PROGRAM.md)**  
Installable clients: **[`docs/INSTALLABLE_CLIENT_STATUS.md`](docs/INSTALLABLE_CLIENT_STATUS.md)**  
Section G project plan (WBS): **[`docs/SECTION_G_PROJECT_PLAN.md`](docs/SECTION_G_PROJECT_PLAN.md)**  
M1 platform API: **[`docs/M1_PLATFORM_STATUS.md`](docs/M1_PLATFORM_STATUS.md)**

| Today (approx.) | Target |
|-----------------|--------|
| Prototype → Internal Alpha foundation (~30–35%) | Supervised beta → controlled production |
| Auth, matter ACL, audit, quarantine, fail-closed citations (partial) | Full M1–M8 gates |
| Unsigned Windows installers (local) | Signed multi-platform releases |

## Quick start (local)

```bash
pip install -r requirements.txt
uvicorn backend.api.main:app --reload --port 8000
# API docs: http://127.0.0.1:8000/docs  →  /v1/platform/*
```

Workbench UI:

```bash
cd apps/platform-ui && npm install && npm run dev
```

Windows installer (unsigned):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows_installer.ps1
```

## Public surfaces

- GitHub: https://github.com/dmang69/bc-legal-ai  
- Hugging Face dataset: https://huggingface.co/datasets/Dmang69/bc-legal-ai  
- Hugging Face Space (static landing): https://huggingface.co/spaces/Dmang69/bc-legal-ai  

Do **not** put confidential client files on public demos. Use synthetic data only.

## Controlling build rule

No feature may bypass an unfinished dependency merely because a demonstration can be made to work.

Verify legislation on **[BC Laws](https://www.bclaws.gov.bc.ca/)** before any reliance or filing.
