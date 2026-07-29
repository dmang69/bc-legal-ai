# BC Legal AI Associate

[![GitHub](https://img.shields.io/badge/GitHub-dmang69%2Fbc--legal--ai-181717?logo=github)](https://github.com/dmang69/bc-legal-ai)
[![HF Space](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Demo-yellow)](https://huggingface.co/spaces/Dmang69/bc-legal-ai-demo)
[![HF Dataset](https://img.shields.io/badge/%F0%9F%A4%97%20Dataset-bc--legal--ai-blue)](https://huggingface.co/datasets/Dmang69/bc-legal-ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Human-supervised** legal research, evidence, drafting, and matter-support platform for British Columbia residential tenancy, judicial review, and related administrative-law workflows.

> **Not a lawyer. Not legal advice.** No solicitor–client relationship is created.  
> Do **not** put confidential client or litigation files on public demos. Use synthetic data only.  
> Verify all legislation on **[BC Laws](https://www.bclaws.gov.bc.ca/)** before any reliance or filing.

**Release:** [v1.0.0](releases/v1.0.0.md) — production-ready **infrastructure** (builds, CI, Docker, auth, health, env docs).  
Still fail-closed for court-ready AI and real-client unsupervised use. See [docs/PRODUCTION_READINESS.md](docs/PRODUCTION_READINESS.md).

---

## Install (v1.0)

### Prerequisites

- Python **3.11+** (CI uses 3.12)
- Node **20+** (platform-ui)
- Optional: Docker, Postgres, Ollama

### Backend

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev,export,pdf]"
# optional multi-user: pip install -e ".[postgres]"
cp .env.example .env
# edit APP_MODE=development
uvicorn backend.api.main:app --reload --port 8000
```

- API docs: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/health  

### Frontend (platform-ui)

```bash
cd apps/platform-ui
npm ci
npm run dev
# http://127.0.0.1:1420  (proxies /v1 → API)
```

Production UI build:

```bash
cd apps/platform-ui
# set VITE_API_BASE_URL=https://api.example.com
npm run build
# publish dist/
```

### Docker

```bash
# Ensure Docker Desktop / engine is running first
docker build -t bc-legal-ai:1.0.0 .
docker run --rm -p 8000:8000 -e APP_MODE=development -e ALA_RATE_LIMIT_DISABLED=1 bc-legal-ai:1.0.0
python scripts/production_smoke.py --base http://127.0.0.1:8000

# Dev stack with Postgres:
docker compose up --build

# Production-style (secrets in .env.production):
# cp .env.production.example .env.production   # edit passwords + CORS_ORIGINS
# .\scripts\cloud-deploy.ps1 -PublicApiUrl https://api.example.com -PublicUiUrl https://app.example.com
```

Cloud runbook: [`docs/CLOUD_DEPLOY.md`](docs/CLOUD_DEPLOY.md)

### Smoke test

```bash
# with API running:
python scripts/production_smoke.py --base http://127.0.0.1:8000
pytest tests/ -q -m "not postgres_required"
```

### Environment & deploy docs

| Doc | Purpose |
|-----|---------|
| [`.env.example`](.env.example) | Variable template |
| [`docs/ENVIRONMENT.md`](docs/ENVIRONMENT.md) | Full env reference |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Docker / cloud / K8s |
| [`docs/SECURITY_REVIEW_V1.md`](docs/SECURITY_REVIEW_V1.md) | Security baseline |
| [`docs/ENTERPRISE_AI_SUITE.md`](docs/ENTERPRISE_AI_SUITE.md) | AI providers & tools |

---

## Try the public demo

| Surface | URL | What it is |
|---------|-----|------------|
| **Static demo (preferred)** | https://huggingface.co/spaces/Dmang69/bc-legal-ai-demo | Client-side triage, JR clock, analytical tagger, design guardrails |
| Dataset | https://huggingface.co/datasets/Dmang69/bc-legal-ai | Skills, lexicon, synthetic fixtures |
| Model card | https://huggingface.co/Dmang69/bc-legal-ai-base | Policy / RAG-first model documentation (not a runnable checkpoint alone) |
| Legacy landing | https://huggingface.co/spaces/Dmang69/bc-legal-ai | Earlier static landing page |

**Demo features**

- **Matter triage** — notice-type deadline flags + forum routing (RTB / JR / BCHRT)
- **JR limitation clock** — 60 days from issuance (ATA s.57(1)) with s.57(2) extension awareness and alternatives when finality/date/enabling Act is uncertain
- **Analytical tagger** — FACT / ALLEGATION / ASSUMPTION / LEGAL ARGUMENT / RECOMMENDATION candidates
- **Design guardrails panel** — the six locked corrections, displayed for auditability
- **Official legislation links** — fail-closed routing to BC Laws, ATA, PIPA, SCCR forms
- **RTA pin self-check** — common wrong-memory section pins

All public-demo logic is **deterministic** and runs **client-side** when published as a static Space (no model inference; no confidential uploads).

**Local preview of the static demo**

```powershell
start "" "D:\AI legal\hf-workspace\spaces\bc-legal-ai-demo-static\index.html"
```

Source in this repo: [`huggingface-space-static/`](huggingface-space-static/)  
(Gradio draft remains under [`huggingface-space/`](huggingface-space/).)

### Auto-deploy (GitHub Actions)

On every push to `main` that changes `huggingface-space-static/**`, workflow
[`.github/workflows/deploy-hf-space.yml`](.github/workflows/deploy-hf-space.yml)
uploads that folder to Space **`Dmang69/bc-legal-ai-demo`** (static SDK).

**One-time setup**

1. Create a Hugging Face **Write** token: https://huggingface.co/settings/tokens  
2. In this GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**  
   - Name: `HF_TOKEN`  
   - Value: the write token  
3. Optional: run the workflow manually via **Actions → Deploy HF Space (static demo) → Run workflow**

If deploy fails with **402**, verify email / billing method on the HF account and confirm the Space SDK is **static** (not Gradio). Static Spaces are free; Gradio/Docker need PRO.

---

## Locked design guardrails

These six corrections are **locked into product design** and must not be reverse-engineered out of demos or APIs.

### 1. Consent is not privilege
Client consent authorizes **specified data processing**. It never automatically creates, waives, or determines solicitor–client or litigation privilege. Privilege analysis is a separate, human-supervised determination.

### 2. Consent withdrawal is not unconditional deletion
Under BC **PIPA**, withdrawal generally operates on **reasonable notice**. Processing may continue where authorized without consent or required by legal obligations.  
- **Immediate:** revoke future optional AI access  
- **Separately assessed:** retention, legal hold, evidentiary obligations

### 3. Correct Supreme Court Civil Rules forms
| Step | Form |
|------|------|
| Petition commencing judicial review | **Form 66** |
| Response to petition | **Form 67** |
| Interlocutory application (e.g. stay) | **Form 32** |
| Application response | **Form 33** |
| Affidavit | **Form 109** |

### 4. JR clock: 60 days from issuance — with alternatives
Ordinary RTB judicial-review limitation: **60 days from issuance of the final decision** (ATA s.57(1)), subject to the extension power and criteria in **ATA s.57(2)**. When finality, issuance date, or enabling legislation is uncertain, the engine **must calculate alternatives** — never a single confident date alone.

### 5. Honest encryption claims
True end-to-end encryption **conflicts** with unrestricted server-side AI analysis of the same content. Choose one honest posture:  
- **on-device classification**, or  
- **controlled server-side decryption** with clear consent, disclosure, audit, and scope  

Never claim both “server-inaccessible E2EE” and unrestricted server-side AI processing.

### 6. The RTB decision archive is not a complete corpus
The official archive covers **specific historical publication ranges and categories**. Absence from the archive is **never** proof that no decision exists. Negative results must be phrased as “not found in the published subset.”

---

## Product description (target platform)

- **[`docs/PRODUCT_DESCRIPTION.md`](docs/PRODUCT_DESCRIPTION.md)** — integrated supervised practice platform  
- **[`docs/CONVERSATIONAL_WORKSPACE_SPEC.md`](docs/CONVERSATIONAL_WORKSPACE_SPEC.md)** — chat-first multi-agent workspace (primary UX)

The platform shell (web/desktop/mobile) is only the **container**. The product is a **conversational AI legal operating environment**: matter chats, research, drafting beside the conversation, specialist agents, evidence links, and human approvals — **not** autonomous legal practice.

## Current implementation status

| Resource | Path |
|----------|------|
| Honest maturity and gaps | [`PRODUCT_STATUS.md`](PRODUCT_STATUS.md) |
| Engineering roadmap | [`docs/PHASE_4_MASTER_ENGINEERING_PROGRAM.md`](docs/PHASE_4_MASTER_ENGINEERING_PROGRAM.md) |
| Installable clients | [`docs/INSTALLABLE_CLIENT_STATUS.md`](docs/INSTALLABLE_CLIENT_STATUS.md) |
| Section G project plan (WBS) | [`docs/SECTION_G_PROJECT_PLAN.md`](docs/SECTION_G_PROJECT_PLAN.md) |
| M1 platform API | [`docs/M1_PLATFORM_STATUS.md`](docs/M1_PLATFORM_STATUS.md) |
| Data model (Postgres/pgvector) | [`docs/DATA_MODEL_AND_EVIDENCE_SCHEMA.md`](docs/DATA_MODEL_AND_EVIDENCE_SCHEMA.md) |

| Today (approx.) | Target |
|-----------------|--------|
| Prototype → Internal Alpha foundation (~30–35%) | Supervised beta → controlled production |
| Auth, matter ACL, audit, quarantine, fail-closed citations (partial) | Full M1–M8 gates |
| Unsigned Windows installers (local) | Signed multi-platform releases |

**Release:** **v1.0.0** — deployable stack + enterprise AI suite on the supervised legal workbench.  
See [`docs/PRODUCTION_READINESS.md`](docs/PRODUCTION_READINESS.md), [`docs/ENTERPRISE_AI_SUITE.md`](docs/ENTERPRISE_AI_SUITE.md).  
**Not** unsupervised legal practice; **not** a lawyer.

## Quick start (local)

**Canonical stack:** API = `backend/` · skills = `skills/` · services = `services/`.  
See [`docs/CANONICAL_STACK.md`](docs/CANONICAL_STACK.md). Non-canonical samples live under [`archive/non-canonical/`](archive/non-canonical/) — do not use them as the product entrypoint.

```bash
pip install -r requirements.txt
# Windows: set APP_MODE=development
export APP_MODE=development
uvicorn backend.api.main:app --reload --port 8000
# API docs: http://127.0.0.1:8000/docs
# Chat: POST /v1/platform/auth/register → /v1/platform/conversations → .../messages
# Skills: GET /v1/platform/skills
```

Workbench UI (optional, later):

```bash
cd apps/platform-ui && npm install && npm run dev
```

Windows installer (unsigned):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows_installer.ps1
```

## Public surfaces

- **GitHub:** https://github.com/dmang69/bc-legal-ai  
- **Hugging Face dataset:** https://huggingface.co/datasets/Dmang69/bc-legal-ai  
- **Hugging Face Space (static demo):** https://huggingface.co/spaces/Dmang69/bc-legal-ai-demo  
- **Hugging Face Space (legacy landing):** https://huggingface.co/spaces/Dmang69/bc-legal-ai  
- **Model documentation:** https://huggingface.co/Dmang69/bc-legal-ai-base  

Do **not** put confidential client files on public demos. Use synthetic data only.

## Controlling build rule

No feature may bypass an unfinished dependency merely because a demonstration can be made to work.

Verify legislation on **[BC Laws](https://www.bclaws.gov.bc.ca/)** before any reliance or filing.
