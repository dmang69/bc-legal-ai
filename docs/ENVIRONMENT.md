# Environment variables reference

**Scope:** BC Legal AI Associate API + platform-ui  
**Template file:** [`.env.example`](../.env.example)  
**Never commit:** `.env`, API keys, PFX passwords, live matter identifiers

## Required by mode

| Variable | development | staging | production | public_demo |
|----------|:-----------:|:-------:|:----------:|:-----------:|
| `APP_MODE` | ✓ | ✓ | ✓ | ✓ `public_demo` |
| `ALA_SQLITE_PATH` *or* `ALA_POSTGRES_URL` | SQLite OK | Postgres | **Postgres** | SQLite/none |
| `CORS_ORIGINS` | optional | ✓ | ✓ | N/A (locked) |
| `ALA_COOKIE_SECURE` | `0` | `1` | **`1`** | `0`/`1` HTTPS |
| `ALA_ALLOW_EXTERNAL_LLM` | optional | review | review | **must be off** |

\* Multi-worker **requires** Postgres. SQLite is single-writer only.

## Core runtime

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_MODE` | `development` | `development` \| `staging` \| `production` \| `public_demo` |
| `CORS_ORIGINS` | localhost list | Comma-separated allowlist; `*` forbidden outside development |
| `ALA_SQLITE_PATH` | `data/ala_platform.sqlite3` | SQLite file path |
| `ALA_POSTGRES_URL` | unset | Postgres DSN → enables multi-worker path |
| `ALA_PG_POOL` | `1` | Enable `psycopg_pool` when Postgres set |
| `ALA_PG_POOL_MIN` / `MAX` | `1` / `10` | Pool bounds |

## Auth / sessions

| Variable | Default | Description |
|----------|---------|-------------|
| `ALA_SESSION_COOKIE` | `ala_session` | HttpOnly session cookie name |
| `ALA_CSRF_COOKIE` | `ala_csrf` | Double-submit CSRF cookie |
| `ALA_SESSION_MAX_AGE` | `43200` | Seconds (12h) |
| `ALA_COOKIE_SECURE` | mode-dependent | Set `1` behind HTTPS |
| `ALA_COOKIE_SAMESITE` | `lax` | `lax` \| `strict` \| `none` |
| `ALA_RATE_LIMIT_*` | see example | Login/register sliding windows |
| `ALA_RATE_LIMIT_DISABLED` | unset | Tests only (`1` to disable) |

## AI providers

| Variable | Description |
|----------|-------------|
| `ALA_MODEL_PROVIDER` | Default provider id (`safe_local`, `ollama`, …) |
| `ALA_OLLAMA_URL` | Ollama base URL |
| `ALA_OLLAMA_MODEL` | Default local model name |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` | OpenAI-compatible |
| `OPENROUTER_API_KEY` | OpenRouter |
| `ANTHROPIC_API_KEY` | Anthropic |
| `ALA_ALLOW_EXTERNAL_LLM` | Must be `1` for live cloud inference |
| `ALA_WEB_RESEARCH` | `1` enables bounded live web research |
| `ALA_BC_LAWS_OFFLINE` | `1` disables BC Laws network fetch |
| `ALA_OCR_DISABLED` | `1` skips Tesseract path |

## Public demo locks

When `APP_MODE=public_demo`, uploads, client data, court-ready exports, persistence, and connectors must remain disabled. Validated by `scripts/validate_deployment_readiness.py`.

## Frontend (Vite)

| Variable | Description |
|----------|-------------|
| `VITE_API_BASE_URL` | API origin (empty string uses Vite proxy in dev) |
| `VITE_APP_MODE` | `private` \| `public_demo` |

## Secrets handling

1. Local: `.env` gitignored; use `.env.example` as template.  
2. CI: GitHub Actions secrets only (`HF_TOKEN` for Space deploy).  
3. Production: cloud secret manager / K8s Secrets — never bake into images.  
4. Rotate any token that appears in logs or chat history.
