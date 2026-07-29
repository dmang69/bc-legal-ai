# Enterprise AI Platform Prototype

This is a **working prototype scaffold** for a multi-model AI platform inspired by the product patterns people expect from tools like ChatGPT, Claude, Copilot, Monica, and Kimi.

## What is included
- chat UI
- workspaces
- multi-chat history
- mode switcher: General / Legal / Research / Code
- prompt library
- file uploads tied to a workspace
- pluggable model gateway
- mock AI responses for local testing
- OpenAI-compatible API support via environment variables
- docs for platform blueprint and UX flows

## Important note
This is a **prototype foundation**, not production parity.

To become production-ready you should upgrade this scaffold to:
- Next.js frontend
- FastAPI + SQLAlchemy + Alembic backend
- PostgreSQL
- Redis queue/rate limiting
- object storage
- hybrid retrieval
- secure auth/SSO/session handling
- audit/permissions/policy controls
- formal evaluation and security testing

## Run locally
```bash
cd enterprise_ai_platform/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Then open:
- `http://127.0.0.1:8000`

## Optional real model integration
By default the app uses `mock` responses.

To use an OpenAI-compatible provider, set:
```bash
export AI_PROVIDER=openai-compatible
export OPENAI_COMPAT_BASE_URL=https://api.openai.com/v1
export OPENAI_API_KEY=your_key_here
export OPENAI_MODEL=gpt-4o-mini
```
You can also point `OPENAI_COMPAT_BASE_URL` at a compatible gateway such as your own model proxy.

## Modes
### General
General-purpose assistant experience.

### Legal
Structured output with legal-information-only framing, useful for issue matrices, chronologies, and drafting support.

### Research
Breaks questions into sub-issues and research plans.

### Code
Copilot-style engineering planning and implementation guidance.

## Folder structure
- `docs/AI_Platform_Enterprise_Blueprint.md`
- `docs/AI_Platform_UX_Screen_Flows.md`
- `backend/main.py`
- `backend/templates/index.html`
- `backend/static/app.js`
- `backend/static/styles.css`
- `backend/requirements.txt`

## Recommended next build steps
1. replace mock auth with real org/user auth
2. move SQLite prototype storage to SQLAlchemy + PostgreSQL
3. add streaming responses
4. add RAG document indexing and retrieval
5. add model comparison mode
6. add artifacts/canvas output system
7. add admin console and RBAC
8. add secure file storage and audit logs
9. add legal matter and evidence workflows
10. split backend into services when usage justifies it