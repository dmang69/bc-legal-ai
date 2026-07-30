# BC Legal AI Platform — Technical Specification

**Version:** 1.0 (aligned with monorepo v1.0.x + AI pillars)  
**Audience:** Engineers, architects, security reviewers  
**Status legend:** **Live** = in repo today · **Target** = enterprise roadmap  

---

## 1. Product summary

Supervised legal workbench for BC residential tenancy, judicial review, and related admin-law workflows.  
AI assists research, triage, drafting, and multi-step planning under **fail-closed** legal locks:

1. Not legal advice / no lawyer impersonation  
2. `court_ready: false` until export gates pass  
3. Matter ACL + ethical walls  
4. No autonomous file / serve / settle / privilege waiver  
5. External server LLMs gated (`ALA_ALLOW_EXTERNAL_LLM`)  
6. Statute truth → BC Laws, not model memory  

---

## 2. High-level architecture

### 2.1 Topology (description)

```
┌─────────────────────────────────────────────────────────────────┐
│  Clients                                                         │
│  Platform UI (Vite/React) · Public static demo · optional Tauri  │
└───────────────┬─────────────────────────────┬───────────────────┘
                │ HTTPS REST                  │ Puter.js (browser)
                ▼                             ▼
┌───────────────────────────┐    ┌────────────────────────────┐
│  API Gateway (FastAPI)    │    │  Puter AI Gateway (user-   │
│  backend.api.main         │    │  pays, 500+ models)        │
└───────────┬───────────────┘    └────────────────────────────┘
            │
    ┌───────┼───────────┬──────────────┬─────────────┐
    ▼       ▼           ▼              ▼             ▼
 Identity  Matters   Conversation   AI Suite    Org Admin
 Sessions  ACL       Orchestrator   Providers   Quotas/Telemetry
    │       │           │              │             │
    └───────┴───────────┴──────┬───────┴─────────────┘
                               ▼
              SQLite / Postgres · Audit ledger · Skills packs
                               │
              Optional: Ollama · Redis · S3/MinIO · HF Buckets
```

**Style:** Modular monolith (FastAPI) + React UI + pluggable **model providers** + **OpenClaw** tool plugins. Not a full multi-repo microservices mesh today; service boundaries are Python packages under `backend/` and `services/`.

### 2.2 Plugin / provider model

| Layer | Mechanism | Live |
|-------|-----------|------|
| LLM providers | `ModelProvider` registry (`puter`, `kimi`, `safe_local`, `ollama`, `openai`, `openrouter`, `anthropic`) | Yes |
| OpenClaw tools | Tool catalog + deterministic executors in `openclaw.py` | Yes |
| Skills | Markdown skill packs resolved by specialist/message | Yes |
| Arena presets | Named provider lineups + client-run merge | Yes |

---

## 3. Core modules

| Module | Responsibility | Primary code / API | Status |
|--------|----------------|--------------------|--------|
| **Conversational Intelligence** | Multi-turn chat, specialists, modes, streaming scaffold | `/v1/platform/conversations/*` | Live |
| **Productivity Workspace** | Summarize, email, creative, research plan, slash tools | `/v1/platform/ai/*` + UI slash bar | Live |
| **Advanced Reasoning** | Deep mode scaffold, safety post-process | `ai_safety.py`, mode `deep` | Live |
| **Local AI Execution** | Ollama HTTP, private_local mode | Provider `ollama` | Live |
| **Developer Intelligence** | Code complete/debug/document | `/v1/platform/ai/code` | Live |
| **Live Retrieval** | Allowlisted web research | `/v1/platform/ai/web-research` | Live (gated) |
| **Multi-Model Evaluation** | Arena AI scores + presets + client Puter/Kimi | `/v1/platform/ai/arena` | Live |
| **Agentic Framework** | OpenClaw plan/execute/memory/HITL | `/v1/platform/ai/openclaw/*` | Live |
| **Security & Governance** | Auth, ACL, audit, org AI settings, quotas | identity, org_admin, audit | Live |
| **Legal engines** | JR clock, citations, Form 66 scaffolds | `services/`, platform modules | Live |
| **GraphQL** | Unified GraphQL layer | — | Target |
| **Full Zero Trust mesh** | Service mesh mTLS, continuous verification | Partial patterns | Target |

### Acceptance criteria (per module) — checklist

**Conversational**
- [x] Create/list conversation; multi-turn history in complete path  
- [x] Matter-scoped ACL enforced when matter set  
- [x] Safety gate on harmful input; disclaimer on outputs  

**OpenClaw**
- [x] Plan + execute tools; high-risk tools need approval  
- [x] Block autonomous file/serve/settle/waive language posture  
- [x] Persist run + optional memory  

**Providers**
- [x] Puter/Kimi client_content path safety-gated  
- [x] External cloud gated by env + org flags  
- [x] Default provider configurable (`ALA_MODEL_PROVIDER`)  

**Arena**
- [x] Multi-provider runs + ranking  
- [x] Client-side Puter/Kimi merge  
- [x] Scores labeled non-Elo  

**Governance**
- [x] Org allowlist + daily quota  
- [x] Usage telemetry estimates  
- [ ] SSO / OIDC production IdP (Target)  
- [ ] GraphQL + webhooks catalog (Target)  

---

## 4. APIs

### 4.1 Authentication

| Pattern | Live |
|---------|------|
| Register / login → bearer token + CSRF for mutating calls | Yes |
| Cookie/session options in platform routes | Partial |
| OAuth2 / OIDC SSO | Target |
| API keys for machine clients | Target |

### 4.2 REST map (selected)

| Area | Methods | Path prefix |
|------|---------|-------------|
| Health | GET | `/health` |
| Auth | POST/GET | `/v1/platform/auth/*` |
| Matters | GET/POST | `/v1/platform/matters` |
| Chat | CRUD + messages | `/v1/platform/conversations/*` |
| Providers | GET | `/v1/platform/workspace/model-providers` |
| Suite | GET | `/v1/platform/ai/suite` |
| Productivity | POST | `/v1/platform/ai/summarize`, `email-draft`, `creative`, `code` |
| Research | POST | `/v1/platform/ai/web-research` |
| Arena | GET/POST | `/v1/platform/ai/arena`, `.../presets` |
| OpenClaw | GET/POST | `/v1/platform/ai/openclaw/*` |
| Complete | POST | `/v1/platform/ai/complete` |
| Org AI | GET/PUT | `/v1/platform/org/ai/*` |

**GraphQL:** not implemented — REST-first; GraphQL is Target for BFF consolidation.

**Model serving API:** abstraction via provider `complete()`; no separate GPU inference service in-box (Ollama external).

**Retrieval API:** `web-research` + skill context; vector RAG is Target.

**Plugin interface:** OpenClaw tool registry + ModelProvider protocol.

**Webhooks:** Target (audit events, export ready, quota alerts).

---

## 5. Data flows

```
1. Ingest (user message / attachment metadata)
      → assess_user_input (block harmful)
2. AuthZ (org, matter ACL)
3. Quota check (org_admin)
4. Persist user message
5. Route:
   a) Slash / productivity tools (deterministic)
   b) OpenClaw plan/execute
   c) Client Puter/Kimi content → enforce_output_safety → persist
   d) Server provider.complete → enforce_output_safety → persist
6. Record usage telemetry
7. Audit ledger append (selected actions)
8. Response to UI (court_ready false)
```

**Indexing / RAG:** skills markdown + allowlisted links today; enterprise vector index Target.

**Data residency:** deploy Postgres + object storage in customer region; browser Puter path implies user-pays vendor processing — document in privacy review.

---

## 6. Security & compliance controls

| Control | Implementation | Status |
|---------|----------------|--------|
| RBAC-ish roles | owner/admin/lawyer patterns on org settings | Live |
| Matter isolation | ACL on matter-scoped chats | Live |
| Encryption in transit | TLS at edge (deploy) | Ops |
| Encryption at rest | Disk / managed DB | Ops |
| Immutable-ish audit | Hash-chained ledger | Live |
| Secret management | Env / deploy secrets; no keys in client for server LLM | Live |
| External LLM gate | `ALA_ALLOW_EXTERNAL_LLM` + org flag | Live |
| Air-gap option | Ollama + safe_local + offline posture | Partial |
| Public demo lockdown | APP_MODE=public_demo, synthetic-only Space | Live |
| Zero Trust continuous auth | Full ZTNA product | Target |
| SSO | OIDC | Target |
| Formal SOC2 package | Process + evidence | Target |

---

## 7. Deployment

| Pattern | Live |
|---------|------|
| Docker image GHCR | Yes |
| Compose (API + optional Postgres/Redis/MinIO) | Yes |
| Uvicorn multi-worker + Postgres | Documented |
| Kubernetes manifests | Scaffold / docs (harden per env) |
| GPU for local models | Host Ollama with GPU |
| CI | GitHub Actions (tests, HF Space static deploy) |
| Multi-tenant | Org_id isolation in app DB |

**Acceptance:** smoke `/health`, register org, chat safe_local, OpenClaw run, Arena preset without secrets.

---

## 8. Operational requirements

| Area | Recommendation |
|------|----------------|
| Monitoring | Health endpoint, reverse-proxy metrics, DB probes |
| Observability | Structured logs + audit ledger; OpenTelemetry Target |
| Cost | Org telemetry estimates; Puter user-pays off-server |
| Latency | Track p95 chat and OpenClaw step duration |
| Model eval | Arena scores + human review samples; not Elo |
| Rollback | Pin GHCR tag; feature flags for external LLM / web research |
| Incident | Disable external LLM; fall back safe_local/Ollama |

---

## 9. Prioritized milestones (engineering)

| P | Milestone | Modules | Acceptance |
|---|-----------|---------|------------|
| P0 | Hardened pilot baseline | Auth, chat, safety, audit, Docker | Pilot checklist green |
| P1 | AI pillars ops-ready | Puter, OpenClaw, Kimi, Arena docs + tests | 18+ suite tests; UI typecheck |
| P2 | Retrieval depth | BC Laws connectors, citation verification depth | Pinpoint verification gates |
| P3 | IdP + multi-worker prod | OIDC, Postgres HA, Redis rate limits | Pen-test prep |
| P4 | Vector RAG (optional) | Matter-scoped embeddings private only | Privacy DPIA signed |
| P5 | GraphQL + webhooks | BFF, event hooks | Partner integration |

---

## 10. Technology constraints

Prefer: FastAPI, React/Vite, Postgres, Docker, Ollama, Puter.js, HF static demo.  
Avoid claiming: full LMSYS Arena, unrestricted autonomous agents, court-ready unsupervised output, E2EE + unrestricted server AI simultaneously.
