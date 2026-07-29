# BC Legal AI — Platform UI

Polished conversational shell for the Enterprise AI suite.

## Features

- Live chat against `backend` (`/v1/platform/conversations`)
- Provider picker (safe_local, Ollama, OpenAI-compatible, ...)
- Slash tools bar: summarize, email, research, code, arena
- Work panel: Tools, Sources, Arena, Org Admin, Agents, Draft
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

Register a synthetic org (password 10+ chars), then chat.

## Build

```bash
npm run typecheck
npm run build
```

Not legal advice. Public demos must stay synthetic-only.
