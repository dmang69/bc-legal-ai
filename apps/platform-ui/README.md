# platform-ui — shared conversational React interface

**Stack:** React · TypeScript · Vite · PWA plugin  
**Modes:** `workbench` | `client` | `self_rep` | `portal`

This app is the shared UI for:

- Browser/PWA portal.
- Tauri 2 Windows/macOS Workbench.
- Tauri 2 Android/iOS Client.

## Current implementation

The current UI has two surfaces:

1. **AI Workspace** — conversational legal workspace connected to the backend safety gateway:
   - conversation modes for general, matter, document, research, drafting, and agent triage;
   - backend `POST /v1/platform/workspace/analyze` safety/citation pathway;
   - fail-closed trust indicators for evidence, law, human review, and privacy;
   - non-operational affordances are displayed as disabled status chips rather than fake buttons;
   - persistent conversation/message APIs are available for authenticated private workbench use.
2. **Platform Admin** — M1–M3 backend smoke-test surface for auth, synthetic matters, fail-closed citation checks, citation audit, and export manifest gates.

Not yet complete: live model orchestration, streaming assistant responses, local Ollama, voice/camera input, external connectors, and autonomous agent execution. These remain blocked until explicit approval, retrieval, citation, privilege, and human-review gates are implemented.

## Development

```bash
npm install
npm run dev        # http://127.0.0.1:5173
npm run typecheck  # TypeScript contract check
npm run build      # dist/ → Tauri frontendDist + static portal host
```

Env: see `.env.example` (`VITE_API_BASE_URL`, `VITE_APP_MODE`).

## Deployment readiness

From the repository root:

```bash
python scripts/validate_deployment_readiness.py        # fast public/HF safety gate
python scripts/validate_deployment_readiness.py --full # safety gate + backend tests + UI build
```

Public/Hugging Face deployments must run with `APP_MODE=public_demo` and must keep public uploads, client data, persistence, connectors, and court-ready exports disabled.

## Safety boundaries

- Synthetic data only in demos.
- Not a lawyer; not legal advice.
- No real client data in public Space or local demo.
- Matter Chat must remain matter-scoped.
- Court-ready outputs require evidence, citation, deadline, privilege, and human approval gates.
