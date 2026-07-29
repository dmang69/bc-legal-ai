# Enterprise AI Suite — architecture & operations

**Product:** BC Legal AI Associate  
**Status:** Operational suite foundations (v0.4.0-alpha)  
**Positioning:** Industry-inspired capabilities **inside** a supervised legal workbench — not a claim to clone proprietary products, and **not** a lawyer.

## Capability map

| Inspiration | Capability in this platform | Primary paths |
|-------------|----------------------------|---------------|
| **Puter AI** | **AI base** — 500+ models, browser `puter.ai.chat()`, user-pays, no server keys | Platform UI + provider `puter` · [docs](https://developer.puter.com/ai/) |
| **OpenClaw** | Multi-step agent harness: plans, tool plugins, memory, HITL gates (fail-closed) | `/v1/platform/ai/openclaw/*`, chat `/claw` · [openclaw.ai](https://openclaw.ai/) |
| **Kimi** | Moonshot long-context / deep analysis (Puter or API) | Provider `kimi`, model `moonshotai/kimi-k2.5` |
| **Arena AI** | Multi-model comparison with legal-aware scores + client Puter/Kimi runs | `/v1/platform/ai/arena`, presets `legal_core` / `kimi_focus` |
| **ChatGPT** | Multi-turn chat, in-session memory, modes, streaming | `/v1/platform/conversations/*` |
| **Monica** | Summarize, email draft, creative, research plan | `/v1/platform/ai/summarize`, `email-draft`, `creative` + chat `/` commands |
| **Claude** | Safety gates, honesty footers, deep reasoning scaffold | `backend/platform/ai_safety.py`, mode `deep` |
| **Ollama** | Local open-source models, private offline path | Provider `ollama`, `ALA_OLLAMA_URL` |
| **Copilot** | Code complete / debug checklist / docs | `/v1/platform/ai/code`, chat `/code` `/debug` |
| **Grok** | Bounded live/public research + curated official links | `/v1/platform/ai/web-research` |
| **Arena** | Side-by-side multi-provider scoring | `/v1/platform/ai/arena` |

Manifest: `GET /v1/platform/ai/suite` (authenticated) — `ai_base: "puter"`.

## Hard enterprise / legal locks (non-negotiable)

1. **Not legal advice** — disclaimers forced on outputs.  
2. **`court_ready: false`** unless full export/manifest gates pass.  
3. **Matter ACL + ethical walls** on matter-scoped chats.  
4. **Server-side external LLMs gated** — require `ALA_ALLOW_EXTERNAL_LLM=1` + API keys.  
5. **Puter** is browser user-pays (no server keys); outputs still safety-gated on persist.  
6. **Ollama preferred** for private_local mode.  
7. **Web research** off by default (`ALA_WEB_RESEARCH=1` to enable); host allowlist.  
8. **No autonomous filing, service, settlement, or privilege waiver.**

## Providers

| ID | Network | Enable |
|----|---------|--------|
| `puter` | browser → Puter | **Default AI base.** Puter.js in UI (`https://js.puter.com/v2/`). User-pays. `ALA_PUTER_MODEL` / `VITE_PUTER_MODEL` |
| `kimi` | browser → Puter / Moonshot API | Long-context Kimi (`moonshotai/kimi-k2.5`). Optional `MOONSHOT_API_KEY` + gate |
| `safe_local` | none | Deterministic orchestrator (offline fallback) |
| `ollama` | localhost | `ALA_OLLAMA_URL` (default `http://127.0.0.1:11434`), `ALA_OLLAMA_MODEL` |
| `openai` | external | `OPENAI_API_KEY`, optional `OPENAI_BASE_URL`, `ALA_ALLOW_EXTERNAL_LLM=1` |
| `openrouter` | external | `OPENROUTER_API_KEY`, `ALA_ALLOW_EXTERNAL_LLM=1` |
| `anthropic` | external | `ANTHROPIC_API_KEY`, `ALA_ALLOW_EXTERNAL_LLM=1` |

Default provider: `ALA_MODEL_PROVIDER` (default **`puter`**).

```bash
# Puter AI base (default) — no server keys; UI loads Puter.js
export ALA_MODEL_PROVIDER=puter
export ALA_PUTER_MODEL=gpt-5-nano

# Local private models
ollama pull llama3.2
export ALA_MODEL_PROVIDER=ollama
export ALA_OLLAMA_MODEL=llama3.2
```

### Puter chat path

1. UI calls `puter.ai.chat(messages, { model })` in the browser.  
2. UI POSTs user text + `client_content` (model output) to `/v1/platform/conversations/{id}/messages` with `provider=puter`.  
3. Backend runs input/output safety gates, persists both messages, records org telemetry.

### OpenClaw agent path

1. `POST /v1/platform/ai/openclaw/run` with `{ goal }` or chat `/claw …`.  
2. Harness builds a multi-step plan (triage, skills, research, JR clock, citations, memory).  
3. High-risk tools require `auto_approve` / human confirmation.  
4. **Never** autonomously files, serves, settles, or waives privilege.

### Kimi path

1. Select provider **Kimi** (or `/kimi`) — default model `moonshotai/kimi-k2.5` via Puter.  
2. Same client_content safety persist path as Puter.  
3. Optional server: `MOONSHOT_API_KEY` + `ALA_ALLOW_EXTERNAL_LLM=1`.

### Arena AI path

1. Slash **Arena AI** or presets (`legal_core`, `kimi_focus`, `private`, `frontier`).  
2. Browser runs Puter/Kimi completions; server runs other providers.  
3. Legal-aware heuristic scores (structure, safety, citation hygiene, completeness).

## Chat slash commands

| Command | Effect |
|---------|--------|
| `/summarize …` | Extractive summary |
| `/email …` | Professional email draft |
| `/creative …` | Creative writing scaffold |
| `/research …` | Research plan |
| `/code …` | Code assist |
| `/debug …` | Debug checklist |
| `/document-code …` | Docstring scaffold |

## Infrastructure alignment

| Layer | Status |
|-------|--------|
| Auth / cookies / rate limits | v0.2–0.3 |
| Postgres multi-worker hooks | v0.3 |
| OCR / BC Laws / Form 66 | v0.3 |
| Multi-provider AI suite | **this doc / v0.4** |
| Horizontal scale | Postgres + uvicorn workers + optional Redis (compose) |
| UI shells | `frontend/client`, `apps/platform-ui`, Tauri |

## Honest limits

This suite **implements architecture and working APIs** for industry-leading *classes* of features. It does **not** reproduce proprietary model weights, LMSYS Elo, full IDE plugins, or unrestricted real-time social firehoses. Production orgs must complete privacy review, DPA, data residency, and pen-test before external LLM traffic.

## Platform UI (v0.4.1)

```bash
uvicorn backend.api.main:app --reload --port 8000
cd apps/platform-ui && npm install && npm run dev
# http://127.0.0.1:1420 — register synthetic org, pick provider, use slash tools / Arena / Admin
```

| UI control | Backend |
|------------|---------|
| Provider select | `ALA_MODEL_PROVIDER` + org allowlist |
| Slash tools | chat orchestrator + `/v1/platform/ai/*` |
| Arena button | `POST /v1/platform/ai/arena` |
| Org Admin tab | `GET/PUT /v1/platform/org/ai/settings`, telemetry |

## Quick verify

```bash
pytest tests/test_ai_suite.py tests/test_conversation.py tests/test_org_admin.py -q
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/v1/platform/ai/suite
```
