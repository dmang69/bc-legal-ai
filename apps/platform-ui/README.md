# BC Legal AI — Platform UI

Polished conversational shell for the Enterprise AI suite.

## AI base: Puter

The default AI provider is **[Puter AI Gateway](https://developer.puter.com/ai/)**:

- Loads `https://js.puter.com/v2/` (see `index.html`)
- Calls `puter.ai.chat()` in the browser (500+ models)
- **User-pays** — no server API keys for Puter traffic
- Responses are still persisted through the backend and run through legal safety gates (`court_ready: false`, not legal advice)

Optional models: set `VITE_PUTER_MODEL` (default `gpt-5-nano`) and `VITE_KIMI_MODEL` (default `moonshotai/kimi-k2.5`).

## Pillars

| Pillar | What it does |
|--------|----------------|
| **Puter** | AI base — 500+ models, user-pays browser inference |
| **OpenClaw** | Multi-step agent plans, tool plugins, memory, HITL (`/claw`, OpenClaw panel) |
| **Kimi** | Moonshot long-context intelligence via Puter (provider `kimi`) |
| **Arena AI** | Multi-model comparison with legal-aware scores + presets |

## Features

- Live chat against `backend` (`/v1/platform/conversations`)
- Provider picker (**Puter**, **Kimi**, safe_local, Ollama, OpenAI-compatible, …)
- Model picker for Puter / Kimi / multi-model providers
- Slash tools: summarize, email, research, code, **OpenClaw**, **Kimi**, **Arena AI**
- Work panel: Tools, Sources, Arena AI, OpenClaw, Org Admin, Agents, Draft
- Org admin: provider allowlists, daily quotas, cost telemetry

## Run

```bash
# Terminal 1 — API
set APP_MODE=development
uvicorn backend.api.main:app --reload --port 8000

# Terminal 2 — UI
cd apps/platform-ui
npm install
npm run dev
```

Open http://127.0.0.1:1420 — Vite proxies `/v1` and `/health` to the API.

Register a synthetic org (password 10+ chars), then chat. First Puter call may prompt a Puter sign-in (user-pays).

## Build

```bash
npm run typecheck
npm run build
```

Not legal advice. Public demos must stay synthetic-only.
