# Canonical development stack

**Focus:** GitHub monorepo development only. Hugging Face is optional/parked.

## Single path to run (local)

| Layer | Path | Role |
|-------|------|------|
| **API (canonical)** | `backend/` | FastAPI modular monolith — auth, matters, chat, JR tools |
| **Skills** | `skills/` | Markdown counsel operating procedures (loaded at chat time) |
| **Deterministic services** | `services/` | JR clock, deadlines, consent, post-resolution, etc. |
| **Legacy/static UI** | `frontend/client/` | Served by backend on `/` in dev |
| **Target UI (later)** | `apps/platform-ui/` | React/Vite workbench — not required to chat today |

### Do **not** use as the BC Legal product entrypoint

| Path | What it is |
|------|------------|
| `apps/api/` | Generic “Enterprise AI Platform” sample (separate product experiment) |
| `apps/web/` | Next.js shell for EAP sample |
| `eap-monorepo/` | Duplicate monorepo tree — do not expand |
| `enterprise_ai_platform/` | Parallel scaffold — do not expand |
| `huggingface*/` | Public demo packaging — parked |

If you are unsure which code to edit for the AI lawyer: **`backend/` + `skills/` + `services/`**.

---

## Run the chat API

From repo root:

```bash
# Windows PowerShell or git-bash from D:\AI legal\bc-legal-ai
pip install -r requirements.txt
set APP_MODE=development
uvicorn backend.api.main:app --reload --port 8000
```

Open:

- API docs: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/health  
- Design locks: http://127.0.0.1:8000/v1/design-locks  
- Skills catalog: http://127.0.0.1:8000/v1/platform/skills  
- Chat capabilities: http://127.0.0.1:8000/v1/platform/chat/capabilities  

### Chat flow (authenticated)

1. `POST /v1/platform/auth/register` — `{org_name, email, password}`  
2. `POST /v1/platform/conversations` — `{title, specialist}`  
   - `specialist`: `jr_counsel` | `rtb_specialist` | `bc_legal_associate` | …  
3. `POST /v1/platform/conversations/{id}/messages` — `{content: "..."}`  

Assistant responses include:

- Skill-grounded structure (Form 66, ATA s.58, etc.)  
- `meta.controls.skills_loaded` — which `skills/*/SKILL.md` files were attached  
- Warnings: not legal advice; WORKING DRAFT  

Optional: put an issuance date `YYYY-MM-DD` in a deadline/JR question to exercise `services/deadlines/jr_clock.py`.

---

## Skill loading

Runtime: `backend/skills_runtime/loader.py`

- Scans `skills/*/SKILL.md`  
- Maps specialists → skills (`SPECIALIST_SKILLS`)  
- Overlays keyword packs (JR, tenancy, BOA, evidence, deadlines)  
- Injects locked design corrections into every skill context block  

Edit counsel behavior by editing skills under `skills/` — especially:

- `skills/supreme-court-civil-counsel/`  
- `skills/bc-judicial-review-guide/`  

---

## Cleanup policy (incremental)

1. **Now:** document canonical path (this file); stop adding features under `apps/api`, `eap-monorepo`, `enterprise_ai_platform`.  
2. **Next:** optional move/archive of those trees to `archive/` once no scripts reference them.  
3. **Do not delete** without checking CI and imports.

---

## Tests

```bash
pytest tests/test_conversation.py tests/test_skills_runtime.py -q
```

---

## Product positioning reminder

Public name: **BC Legal AI Associate**  
Internal nickname only: “AI lawyer” — do not use publicly as a license claim.  
Not legal advice. SRL-safe drafting support with human gates.
