# Enterprise AI Platform — Monorepo

**Status:** Tier 0 complete. Multi-tenant, RAG, streaming, and everything above
Tier 0 in the roadmap are unbuilt.

A multi-model AI workspace scaffold. FastAPI backend on Postgres, Next.js 15
frontend, deployable via `docker compose`.

## Layout

```
apps/
├── api/                    FastAPI + SQLAlchemy 2.0 + Alembic
│   ├── app/
│   │   ├── main.py         entry point (create_app, seed, health)
│   │   ├── config.py       pydantic-settings from env
│   │   ├── db/base.py      engine, session, declarative Base
│   │   ├── models/         SQLAlchemy models (users, sessions, ...)
│   │   ├── routers/        auth, workspace
│   │   └── services/       auth logic, dependencies
│   ├── alembic/            migrations
│   ├── tests/              pytest against a real Postgres
│   ├── Dockerfile
│   └── requirements.txt
├── web/                    Next.js 15 App Router
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx        redirect based on auth
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   └── chat/page.tsx   sidebar + thread + composer
│   ├── lib/api.ts          typed client, cookie sessions
│   ├── Dockerfile
│   └── package.json
packages/
└── shared-types/           (empty; reserved for API contract sharing)
docker-compose.yml          Postgres + api + web
.env.example
```

## Run with Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

Then open http://localhost:3000. Register the first user (auto-admin).

The api container runs `alembic upgrade head` on startup; migrations always
apply before the app serves requests.

## Run locally without Docker

**API:**

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Postgres must be reachable
export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/enterprise_ai"

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Web:**

```bash
cd apps/web
npm install --legacy-peer-deps       # or pnpm install
npm run dev                          # http://localhost:3000
```

The web app expects the API at `NEXT_PUBLIC_API_BASE_URL` (default
`http://localhost:8000`).

## Auth model

**Cookie sessions**, not JWT bearer tokens. The Phase 1 semantics from the
previous scaffold are preserved:

- Argon2id password hashing
- Opaque server-side session tokens, stored in the `sessions` table
- `eap_session` httpOnly SameSite=Lax cookie
- Rolling refresh (6h since last use → extend expiry to +7 days)
- Sessions revocable server-side (single, all-for-user, or per-token)

The Next.js client uses `credentials: 'include'` on every request. A 401 from
the API triggers a client-side redirect to `/login`.

### First user, then closed

The first user to register becomes admin. Subsequent registration is closed
unless one of these env vars is set:

- `EAP_ENABLE_REGISTRATION=1` — anyone can register
- `EAP_BOOTSTRAP_TOKEN=<secret>` — anyone with the token can register

## Environment

See `.env.example` for the full list. The important ones:

| Var | Default | Purpose |
|-----|---------|---------|
| `DATABASE_URL` | postgres://... in compose | SQLAlchemy DSN |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Comma-separated allowed origins |
| `EAP_COOKIE_SECURE` | `0` | Set `1` when serving over HTTPS |
| `AI_PROVIDER` | `mock` | Or `openai-compatible` |
| `OPENAI_API_KEY` | | For openai-compatible provider |
| `OPENAI_COMPAT_BASE_URL` | | e.g. `https://api.openai.com/v1` |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Where the browser hits the API |

## Verified behavior (10 pytest tests + 8 stack tests)

All confirmed against a live Postgres:

- API health endpoint is public
- Unauthenticated `/api/*` returns 401
- First registration succeeds and assigns admin role
- Session cookie enables subsequent authenticated requests
- Bootstrap payload includes user, workspaces, chats, seeded prompts
- Second registration blocked by default
- Weak / wrong passwords rejected
- Workspace, chat, message flow: create → send → assistant reply persisted
- Admin-only endpoints gated by role
- Logout revokes the session; next request returns 401
- Next.js builds all 4 routes cleanly, TypeScript strict passes

## What's not in this tier

Per the roadmap:

- **Tier 1** — organizations, teams, RBAC beyond admin/user, invite flow
- **Tier 2** — streaming responses (SSE), Anthropic adapter, retries, rate limits
- **Tier 3** — RAG with pgvector, document ingestion, citations
- **Tier 4** — artifacts, compare mode, templates, message actions
- **Tier 5** — admin console UI
- **Tier 6** — legal matter workflows (or integrate `bc-legal-ai`)
- **Tier 7** — CSRF middleware, login rate limiting, password reset
- **Tier 8** — SSO, MFA, billing
- **Tier 9** — production compose, K8s manifests, backups, observability

See the audit doc for the detailed 56-item breakdown.

## API reference

```
Public:
  GET   /api/health

Auth:
  POST  /api/auth/register
  POST  /api/auth/login
  POST  /api/auth/logout
  POST  /api/auth/logout-all
  GET   /api/auth/me

Workspace (requires session):
  GET   /api/bootstrap
  GET   /api/workspaces
  POST  /api/workspaces
  GET   /api/chats
  POST  /api/chats
  GET   /api/chats/{chat_id}
  POST  /api/chats/{chat_id}/messages
  GET   /api/files
  POST  /api/files
  GET   /api/prompts
  POST  /api/prompts
  GET   /api/settings
  POST  /api/settings

Admin (requires admin role):
  GET   /api/admin/health
```

Interactive docs at http://localhost:8000/docs when the API is running.

## Running the tests

```bash
# Postgres must be up
export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/enterprise_ai"
cd apps/api
pytest tests/ -v
```

Expected: 10 passed.

## Migrations

```bash
cd apps/api
alembic upgrade head            # apply
alembic revision --autogenerate -m "add teams"    # generate from model changes
alembic downgrade -1            # roll back one step
```

## License

Same as source repository — MIT unless noted otherwise.
