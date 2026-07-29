# Enterprise AI Suite — architecture & operations

**Product:** BC Legal AI Associate  
**Status:** Operational suite foundations (v0.4.0-alpha)  
**Positioning:** Industry-inspired capabilities **inside** a supervised legal workbench — not a claim to clone proprietary products, and **not** a lawyer.

## Capability map

| Inspiration | Capability in this platform | Primary paths |
|-------------|----------------------------|---------------|
| **ChatGPT** | Multi-turn chat, in-session memory, modes, streaming | `/v1/platform/conversations/*` |
| **Monica** | Summarize, email draft, creative, research plan | `/v1/platform/ai/summarize`, `email-draft`, `creative` + chat `/` commands |
| **Claude** | Safety gates, honesty footers, deep reasoning scaffold | `backend/platform/ai_safety.py`, mode `deep` |
| **Ollama** | Local open-source models, private offline path | Provider `ollama`, `ALA_OLLAMA_URL` |
| **Copilot** | Code complete / debug checklist / docs | `/v1/platform/ai/code`, chat `/code` `/debug` |
| **Grok** | Bounded live/public research + curated official links | `/v1/platform/ai/web-research` |
| **Arena** | Side-by-side multi-provider scoring | `/v1/platform/ai/arena` |

Manifest: `GET /v1/platform/ai/suite` (authenticated).

## Hard enterprise / legal locks (non-negotiable)

1. **Not legal advice** — disclaimers forced on outputs.  
2. **`court_ready: false`** unless full export/manifest gates pass.  
3. **Matter ACL + ethical walls** on matter-scoped chats.  
4. **External LLMs gated** — require `ALA_ALLOW_EXTERNAL_LLM=1` + API keys.  
5. **Ollama preferred** for private_local mode.  
6. **Web research** off by default (`ALA_WEB_RESEARCH=1` to enable); host allowlist.  
7. **No autonomous filing, service, settlement, or privilege waiver.**

## Providers

| ID | Network | Enable |
|----|---------|--------|
| `safe_local` | none | default deterministic orchestrator |
| `ollama` | localhost | `ALA_OLLAMA_URL` (default `http://127.0.0.1:11434`), `ALA_OLLAMA_MODEL` |
| `openai` | external | `OPENAI_API_KEY`, optional `OPENAI_BASE_URL`, `ALA_ALLOW_EXTERNAL_LLM=1` |
| `openrouter` | external | `OPENROUTER_API_KEY`, `ALA_ALLOW_EXTERNAL_LLM=1` |
| `anthropic` | external | `ANTHROPIC_API_KEY`, `ALA_ALLOW_EXTERNAL_LLM=1` |

Default provider: `ALA_MODEL_PROVIDER` (default `safe_local`).

```bash
# Local private models
ollama pull llama3.2
export ALA_MODEL_PROVIDER=ollama
export ALA_OLLAMA_MODEL=llama3.2
```

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

## Quick verify

```bash
pytest tests/test_ai_suite.py tests/test_conversation.py -q
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/v1/platform/ai/suite
```
