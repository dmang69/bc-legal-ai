# BC Legal AI Associate

[![CI](https://github.com/dmang69/bc-legal-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/dmang69/bc-legal-ai/actions/workflows/ci.yml)
[![GHCR](https://img.shields.io/badge/ghcr.io-dmang69%2Fbc--legal--ai-blue?logo=docker)](https://github.com/dmang69/bc-legal-ai/pkgs/container/bc-legal-ai)
[![Release](https://img.shields.io/github/v/release/dmang69/bc-legal-ai?include_prereleases)](https://github.com/dmang69/bc-legal-ai/releases)
[![HF Demo](https://img.shields.io/badge/%F0%9F%A4%97%20Demo-Space-yellow)](https://huggingface.co/spaces/Dmang69/bc-legal-ai-demo)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Human-supervised **legal research, evidence, drafting, and matter-support** platform for British Columbia residential tenancy, judicial review, and related administrative-law workflows.

> **Not a lawyer. Not legal advice.** No solicitor–client relationship is created.  
> Do **not** put confidential client files on public demos — synthetic data only.  
> Verify legislation on **[BC Laws](https://www.bclaws.gov.bc.ca/)** before any reliance or filing.

**Current release:** [v1.0.1](releases/v1.0.1.md) · Production-ready **infrastructure** + supervised workbench.  
See [docs/PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md).

---

## Quick start (Docker / GHCR)

The simplest way to run the API — no local Python install required:

```bash
docker run --rm -p 8000:8000 \
  -e APP_MODE=development \
  ghcr.io/dmang69/bc-legal-ai:latest
```

| | |
|---|---|
| API docs | http://127.0.0.1:8000/docs |
| Health | http://127.0.0.1:8000/health |

| Image tag | Meaning |
|-----------|---------|
| `latest` | Latest versioned release |
| `edge` | Rolling build from `main` |
| `1.0.1` | Pin a specific release |

```bash
# Compose (pull only)
docker compose -f docker-compose.ghcr.yml up

# Optional smoke test (from this repo)
python scripts/production_smoke.py --base http://127.0.0.1:8000
```

Full GHCR guide: **[docs/GHCR.md](docs/GHCR.md)**

If the package is private, log in once: `echo $CR_PAT | docker login ghcr.io -u USERNAME --password-stdin`  
Then set package visibility to **Public** under GitHub → Packages for anonymous pulls.

---

## What you get

| Area | Capabilities |
|------|----------------|
| **Matters & auth** | Register/login, org isolation, matter ACL, ethical walls, hash-chained audit |
| **Conversational workspace** | Multi-turn chat, specialists, modes, streaming, skill-grounded JR/RTB support |
| **Enterprise AI suite** | **Puter** AI base + **OpenClaw** agents + **Kimi** long-context + **Arena AI** comparison; Ollama / OpenAI / Anthropic fallbacks |
| **Legal tooling** | JR clock (ATA s.57), citation fail-closed gates, Form 66 scaffold, BC Laws fetch path |
| **Platform UI** | Live chat shell — Puter default, model picker, slash-tools, work panel, org admin |
| **Ops** | Docker, Compose, GHCR publish, CI, portable SQLite + Postgres schema |

Architecture entrypoint: **`backend/`** + **`skills/`** + **`services/`**  
Canonical path: [docs/CANONICAL_STACK.md](docs/CANONICAL_STACK.md)

---

## AI suite (four pillars)

Default AI base is **[Puter](https://developer.puter.com/ai/)** (browser Puter.js, user-pays, no server API keys). Three complementary pillars expand agent, long-context, and multi-model workflows — all under legal fail-closed gates.

| Pillar | Role | Entry points |
|--------|------|----------------|
| **Puter** | AI base — 500+ models via `puter.ai.chat()`, user-pays in the browser | Provider `puter` · [Puter AI docs](https://developer.puter.com/ai/) |
| **OpenClaw** | Multi-step agent harness: plans, tool plugins, session memory, human approval for high-risk tools | Chat `/claw …` · `POST /v1/platform/ai/openclaw/run` · [openclaw.ai](https://openclaw.ai/) (inspired by) |
| **Kimi** | Moonshot long-context / deep analysis (`moonshotai/kimi-k2.5` via Puter) | Provider `kimi` · optional `MOONSHOT_API_KEY` + `ALA_ALLOW_EXTERNAL_LLM=1` |
| **Arena AI** | Side-by-side model comparison with legal-aware heuristic scores (not LMSYS Elo) | Slash **Arena AI** · presets `legal_core`, `kimi_focus`, `private`, `frontier` · `POST /v1/platform/ai/arena` |

**Safety locks (non-negotiable):**

- Not legal advice · `court_ready: false` unless full export gates pass  
- OpenClaw never autonomously files, serves, settles, or waives privilege  
- Server-side OpenAI/Anthropic/Moonshot require privacy review + `ALA_ALLOW_EXTERNAL_LLM=1`  
- Puter/Kimi browser completions are still safety-gated and persisted by the API  

Full provider matrix, env vars, and paths: **[docs/ENTERPRISE_AI_SUITE.md](docs/ENTERPRISE_AI_SUITE.md)**

```bash
# Defaults (see .env.example)
ALA_MODEL_PROVIDER=puter
ALA_PUTER_MODEL=gpt-5-nano
ALA_KIMI_MODEL=moonshotai/kimi-k2.5
# VITE_PUTER_MODEL / VITE_KIMI_MODEL for the platform UI build
```

---

## Install on every platform

**Full guide:** **[INSTALL.md](INSTALL.md)** · Status: [docs/INSTALLABLE_CLIENT_STATUS.md](docs/INSTALLABLE_CLIENT_STATUS.md)

| Platform | Install method | Build / run |
|----------|----------------|-------------|
| **Windows** | Setup **`.exe`** (NSIS) · optional **`.msi`** | `scripts\build_windows_installer.ps1` → `releases\windows\` |
| **macOS** | **`.dmg`** / **`.app`** | Tauri on a Mac: `npx tauri build --config src-tauri/tauri.macos.conf.json` |
| **Linux** | Docker API · Tauri AppImage/deb · browser | `docker compose up` or `npx tauri build` on Linux |
| **Android** | Play **`.aab`** · test **`.apk`** | `apps/desktop-mobile` → `npm run android:init` / `android:dev` / `tauri android build` |
| **iPhone / iPad** | TestFlight / App Store **`.ipa`** | Mac + Xcode → `npm run ios:init` / `ios:dev` / `tauri ios build` |
| **Google Chrome / Edge** | **Install as app (PWA)** | Host `apps/platform-ui` on **HTTPS** → Chrome ⋮ → Install page as app |
| **No install (demo)** | Browser only | https://huggingface.co/spaces/Dmang69/bc-legal-ai |

All native/PWA clients need a **private API** (Docker or uvicorn). Signed store binaries are **built from this repo**; public GitHub Release signing is org-gated ([docs/SIGNING_AND_DISTRIBUTION.md](docs/SIGNING_AND_DISTRIBUTION.md)).

**Upgrades:** Windows/macOS/Linux use the same product id + higher version (NSIS/MSI in-place or Tauri auto-updater via GitHub `latest.json`). Android/iOS use store version codes. Chrome PWA updates when you redeploy the Portal. Details: **[docs/UPGRADES.md](docs/UPGRADES.md)** · verify: `cd apps/desktop-mobile && npm run verify:config`.

### Windows Setup.exe (Workbench)

```powershell
# Prerequisites: Node 20+, Rust, WebView2, VS C++ build tools, API on :8000
powershell -ExecutionPolicy Bypass -File scripts\build_windows_installer.ps1
# → releases\windows\*.exe (+ checksums.txt)
# Sign before distribution: scripts\sign_windows_installer.ps1
```

Dev without installer:

```text
START-API.cmd
START-UI.cmd
```

### macOS

```bash
cd apps/platform-ui && npm ci && npm run build
cd ../desktop-mobile && npm ci
npx tauri build --config src-tauri/tauri.macos.conf.json
# → src-tauri/target/release/bundle/dmg/
```

### Linux

```bash
# Server API
docker run --rm -p 8000:8000 -e APP_MODE=development ghcr.io/dmang69/bc-legal-ai:latest
# Desktop (optional, on a Linux builder)
cd apps/desktop-mobile && npx tauri build
```

### Android

```bash
cd apps/desktop-mobile
npm ci
npm run android:init   # first time
# set VITE_API_BASE_URL to a URL the phone can reach (not 127.0.0.1)
npm run android:dev
# release: npx tauri android build  → .aab / .apk
```

### iPhone / iPad

```bash
# Requires Mac + Xcode + Apple Developer Program
cd apps/desktop-mobile
npm run ios:init       # first time
npm run ios:dev
# release: npx tauri ios build → Archive → TestFlight
```

### Google Chrome (installable Portal)

```bash
cd apps/platform-ui
npm ci && npm run build
# serve dist/ over HTTPS, then Chrome → Install page as app
# manifest: public/manifest.webmanifest
```

---

## Public demo (no install)

| Surface | URL |
|---------|-----|
| **Static HF Space (primary)** | https://huggingface.co/spaces/Dmang69/bc-legal-ai |
| Mirror | https://huggingface.co/spaces/Dmang69/bc-legal-ai-demo |
| Dataset | https://huggingface.co/datasets/Dmang69/bc-legal-ai |
| Model card (docs) | https://huggingface.co/Dmang69/bc-legal-ai-base |

Demo features (deterministic, client-side, **no confidential uploads**):

- Matter triage and forum routing (RTB / JR / BCHRT)
- JR limitation clock (ATA s.57) with alternatives when dates/finality are uncertain
- FACT / ALLEGATION / ARGUMENT tagging
- Design guardrails panel and BC Laws / form links

Source: [`huggingface-space-static/`](huggingface-space-static/) · CI: `.github/workflows/deploy-hf-space.yml`

---

## Develop from source

### Prerequisites

- Python **3.11+** (CI: 3.12)
- Node **20+** (for platform-ui / Tauri)
- Optional: Docker, Postgres, [Ollama](https://ollama.com), Rust (desktop/mobile installers)

### API

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev,export,pdf]"
# multi-user / multi-worker: pip install -e ".[postgres]"
cp .env.example .env
# set APP_MODE=development

uvicorn backend.api.main:app --reload --port 8000
```

### Platform UI

```bash
cd apps/platform-ui
npm ci
npm run dev
# http://127.0.0.1:1420  (proxies /v1 → API)
```

### Local stack (API + Postgres + Redis + MinIO)

```bash
docker compose up --build
```

### Cloud / production

```powershell
cp .env.production.example .env.production
# set POSTGRES_PASSWORD, ALA_POSTGRES_URL, CORS_ORIGINS=https://app.example.com

.\scripts\cloud-deploy.ps1 `
  -PublicApiUrl https://api.example.com `
  -PublicUiUrl https://app.example.com
```

See [docs/CLOUD_DEPLOY.md](docs/CLOUD_DEPLOY.md) and [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

### Tests & quality gates

```bash
pytest tests/ -q -m "not postgres_required"
python scripts/scan_confidential.py .
APP_MODE=public_demo python scripts/validate_deployment_readiness.py
cd apps/platform-ui && npm run build
```

---

## Locked design guardrails

These six rules are **product locks** — demos and APIs must not reverse them.

| # | Rule |
|---|------|
| 1 | **Consent ≠ privilege** — consent authorizes processing; privilege is a separate analysis |
| 2 | **Withdrawal ≠ instant deletion** — PIPA reasonable notice; holds and legal duties may apply |
| 3 | **Forms:** petition **Form 66** · response **Form 67** · interlocutory **32/33** · affidavit **109** |
| 4 | **JR clock:** 60 days from **issuance** (ATA s.57(1)); always surface alternatives when uncertain |
| 5 | **Honest encryption** — no false “E2EE + unrestricted server AI” claims |
| 6 | **RTB archive is partial** — absence ≠ “no decision exists” |

---

## Documentation map

| Doc | Purpose |
|-----|---------|
| [docs/GHCR.md](docs/GHCR.md) | Container distribution |
| [docs/PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md) | v1.0 gate checklist |
| [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) | All environment variables |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Docker, K8s, cloud |
| [docs/CLOUD_DEPLOY.md](docs/CLOUD_DEPLOY.md) | TLS + Postgres + CORS runbook |
| [docs/SECURITY_REVIEW_V1.md](docs/SECURITY_REVIEW_V1.md) | Security baseline |
| [docs/ENTERPRISE_AI_SUITE.md](docs/ENTERPRISE_AI_SUITE.md) | AI providers & tools |
| [docs/CANONICAL_STACK.md](docs/CANONICAL_STACK.md) | What code to edit |
| [PRODUCT_STATUS.md](PRODUCT_STATUS.md) | Honest maturity assessment |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution notes |
| [SECURITY.md](SECURITY.md) | Security policy |

---

## Project layout (high level)

```text
backend/                    FastAPI modular monolith (canonical API)
  platform/model_providers  Puter, Kimi, Ollama, OpenAI, Anthropic…
  platform/openclaw.py      OpenClaw-style agent harness
  platform/arena.py         Arena AI multi-model comparison
skills/                     Counsel / tenancy / JR operating procedures
services/                   Deterministic engines (deadlines, HITL, post-resolution)
apps/platform-ui/           React workbench (Puter, OpenClaw, Kimi, Arena, org admin)
frontend/client/            Lightweight static client served by API
huggingface-space-static/   Public deterministic demo
docs/                       Engineering & ops documentation
archive/                    Non-canonical samples (do not use as entrypoint)
```

---

## Status (honest)

| Layer | v1.0 posture |
|-------|----------------|
| Build / CI / Docker / GHCR | Production-ready infrastructure |
| Auth, ACL, audit, smoke APIs | Deployable for supervised / synthetic use |
| Court-ready AI, unsupervised advice | **Fail-closed — not offered** |
| Real-client multi-tenant SaaS | Requires org pen-test, PIA, ops (not claimed by this tag) |

**Controlling build rule:** no feature may bypass an unfinished safety dependency just to make a demo look complete.

---

## License

[MIT](LICENSE) — see also [SECURITY.md](SECURITY.md) for reporting guidance.

---

## Links

- **Source:** https://github.com/dmang69/bc-legal-ai  
- **Container:** https://github.com/dmang69/bc-legal-ai/pkgs/container/bc-legal-ai  
- **Demo:** https://huggingface.co/spaces/Dmang69/bc-legal-ai-demo  
- **BC Laws:** https://www.bclaws.gov.bc.ca/  
