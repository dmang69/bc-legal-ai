import json
import os
import re
import sqlite3
import textwrap
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "platform.db"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Enterprise AI Platform Prototype")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class WorkspaceCreate(BaseModel):
    name: str
    kind: str = "general"


class ChatCreate(BaseModel):
    workspace_id: int
    title: str = "New Chat"


class PromptCreate(BaseModel):
    title: str
    body: str
    scope: str = "personal"


class MessageCreate(BaseModel):
    content: str
    mode: str = "general"
    model_id: str = "mock-general"


class SettingUpdate(BaseModel):
    key: str
    value: str


DEFAULT_MODELS = [
    {"id": "mock-general", "label": "Platform Default", "provider": "mock", "modes": ["general", "research"]},
    {"id": "mock-legal", "label": "Legal Counsel", "provider": "mock", "modes": ["legal"]},
    {"id": "mock-code", "label": "Code Copilot", "provider": "mock", "modes": ["code"]},
    {"id": os.getenv("OPENAI_MODEL", "openai-compatible"), "label": "OpenAI-Compatible", "provider": "openai-compatible", "modes": ["general", "legal", "research", "code"]},
]

DEFAULT_PROMPTS = [
    (
        "Legal issue matrix",
        "Organize the problem into Facts, Assumptions, Issues, Governing Law, Evidence Gaps, Counterarguments, and Requested Remedy.",
        "team",
    ),
    (
        "Case chronology",
        "Turn the record into a clean chronology with date, event, source, and why it matters.",
        "team",
    ),
    (
        "Code review",
        "Review the code for correctness, security, maintainability, and testing gaps.",
        "team",
    ),
]


SYSTEM_GUIDANCE = {
    "general": "You are a professional enterprise AI assistant. Be useful, organized, and concise.",
    "legal": (
        "You are a legal information and drafting support assistant. Never invent facts. "
        "Do not present unsettled law as certain. Separate FACT, ASSUMPTION, ISSUE, LAW, ANALYSIS, and REMEDY. "
        "Output suitable for counsel refinement before filing."
    ),
    "research": "You are a research analyst. Break questions into sub-issues, state uncertainties, and organize findings clearly.",
    "code": "You are a senior engineering copilot. Provide implementation advice, risks, tests, and clean code suggestions.",
}


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = db()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS workspaces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            kind TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workspace_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            mode TEXT NOT NULL,
            model_id TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workspace_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            content_type TEXT,
            stored_path TEXT NOT NULL,
            extracted_text TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            scope TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()

    existing = cur.execute("SELECT COUNT(*) AS c FROM prompts").fetchone()["c"]
    if existing == 0:
        cur.executemany(
            "INSERT INTO prompts (title, body, scope, created_at) VALUES (?, ?, ?, ?)",
            [(t, b, s, now_iso()) for t, b, s in DEFAULT_PROMPTS],
        )
        conn.commit()

    existing_workspaces = cur.execute("SELECT COUNT(*) AS c FROM workspaces").fetchone()["c"]
    if existing_workspaces == 0:
        cur.execute(
            "INSERT INTO workspaces (name, kind, created_at) VALUES (?, ?, ?)",
            ("Default Workspace", "general", now_iso()),
        )
        workspace_id = cur.lastrowid
        cur.execute(
            "INSERT INTO chats (workspace_id, title, created_at) VALUES (?, ?, ?)",
            (workspace_id, "Welcome Chat", now_iso()),
        )
        chat_id = cur.lastrowid
        cur.execute(
            "INSERT INTO messages (chat_id, role, content, mode, model_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                chat_id,
                "assistant",
                "Welcome. This prototype includes workspaces, chat history, modes, prompts, uploads, and a pluggable model gateway.",
                "general",
                "mock-general",
                now_iso(),
            ),
        )
        conn.commit()
    conn.close()


def audit(event_type: str, payload: dict) -> None:
    conn = db()
    conn.execute(
        "INSERT INTO audits (event_type, payload, created_at) VALUES (?, ?, ?)",
        (event_type, json.dumps(payload), now_iso()),
    )
    conn.commit()
    conn.close()


def fetch_workspaces() -> List[dict]:
    conn = db()
    rows = conn.execute("SELECT * FROM workspaces ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def fetch_chats(workspace_id: Optional[int] = None) -> List[dict]:
    conn = db()
    if workspace_id:
        rows = conn.execute("SELECT * FROM chats WHERE workspace_id = ? ORDER BY id DESC", (workspace_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM chats ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def fetch_messages(chat_id: int) -> List[dict]:
    conn = db()
    rows = conn.execute("SELECT * FROM messages WHERE chat_id = ? ORDER BY id ASC", (chat_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def fetch_files(workspace_id: Optional[int] = None) -> List[dict]:
    conn = db()
    if workspace_id:
        rows = conn.execute("SELECT * FROM files WHERE workspace_id = ? ORDER BY id DESC", (workspace_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM files ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def fetch_prompts() -> List[dict]:
    conn = db()
    rows = conn.execute("SELECT * FROM prompts ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def bootstrap_payload() -> dict:
    workspaces = fetch_workspaces()
    active_workspace_id = workspaces[0]["id"] if workspaces else None
    chats = fetch_chats(active_workspace_id) if active_workspace_id else []
    active_chat_id = chats[0]["id"] if chats else None
    return {
        "models": DEFAULT_MODELS,
        "workspaces": workspaces,
        "active_workspace_id": active_workspace_id,
        "chats": chats,
        "active_chat_id": active_chat_id,
        "messages": fetch_messages(active_chat_id) if active_chat_id else [],
        "files": fetch_files(active_workspace_id) if active_workspace_id else [],
        "prompts": fetch_prompts(),
        "settings": {
            "provider": os.getenv("AI_PROVIDER", "mock"),
            "openai_compatible_enabled": bool(os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_COMPAT_BASE_URL")),
        },
    }


def truncate(text: str, length: int = 180) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= length else text[: length - 3] + "..."


def relevant_workspace_context(chat_id: int) -> str:
    conn = db()
    chat = conn.execute("SELECT * FROM chats WHERE id = ?", (chat_id,)).fetchone()
    if not chat:
        conn.close()
        return ""
    files = conn.execute(
        "SELECT filename, extracted_text FROM files WHERE workspace_id = ? ORDER BY id DESC LIMIT 5",
        (chat["workspace_id"],),
    ).fetchall()
    conn.close()
    snippets = []
    for row in files:
        text = row["extracted_text"] or ""
        if text.strip():
            snippets.append(f"{row['filename']}: {truncate(text, 240)}")
    if not snippets:
        return ""
    return "\n\nWorkspace file snippets:\n- " + "\n- ".join(snippets)


def build_mock_response(mode: str, user_message: str, chat_id: int) -> str:
    ctx = relevant_workspace_context(chat_id)
    if mode == "legal":
        return textwrap.dedent(
            f"""
            LEGAL INFORMATION / DRAFTING SUPPORT ONLY

            FACT
            - User request: {user_message}

            ASSUMPTIONS / MISSING VERIFICATION
            - I do not have the full record, all governing documents, or verified authorities.
            - Any filing, legal conclusion, or deadline must be independently checked before use.

            ISSUE FRAME
            - Identify the governing forum, legislation, deadlines, and evidentiary record.
            - Separate proven facts from allegations and strategy from evidence.

            WORKING ANALYSIS
            - Start by extracting a chronology and issue matrix.
            - Confirm jurisdiction, applicable procedural rules, limitation or filing deadlines, and available remedies.
            - If this matter involves documents, convert them into a structured evidence bundle and chronology.

            DRAFTING OUTPUT
            - I can produce: chronology, issue list, affidavit draft, submission outline, factum skeleton, petition skeleton, witness plan, or evidence chart.

            RECOMMENDED NEXT STEP
            - Upload the relevant notices, agreements, decisions, correspondence, and chronology notes.
            - Then request a specific work product, e.g. “draft petition”, “build JR grounds table”, or “turn this record into hearing submissions”.
            {ctx}
            """
        ).strip()
    if mode == "research":
        return textwrap.dedent(
            f"""
            RESEARCH MODE

            Primary Question
            - {user_message}

            Sub-Issues
            1. What exactly needs to be answered?
            2. What sources or authorities are required?
            3. What facts are missing or assumed?
            4. What competing interpretations or risks exist?

            Suggested Research Plan
            - define jurisdiction and date range
            - identify statute / rule / policy sources
            - identify binding vs persuasive authorities
            - extract contradictions and unresolved questions
            - produce a memo with citations and verification flags
            {ctx}
            """
        ).strip()
    if mode == "code":
        return textwrap.dedent(
            f"""
            CODE COPILOT MODE

            Request
            - {user_message}

            Recommended Structure
            - clarify the target stack and runtime
            - define interfaces and data models first
            - isolate provider integrations behind adapters
            - add tests for core workflows and edge cases

            Engineering Checklist
            - correctness
            - security
            - performance
            - maintainability
            - observability
            - DX and documentation
            {ctx}
            """
        ).strip()
    return textwrap.dedent(
        f"""
        GENERAL ASSISTANT MODE

        I understood your request as:
        - {user_message}

        Suggested next actions:
        1. Clarify the deliverable you want.
        2. Attach relevant files if the answer should use workspace context.
        3. Switch modes if you want legal, research, or code-specific output.

        This prototype supports workspaces, prompts, uploads, and a pluggable model gateway.
        {ctx}
        """
    ).strip()


def openai_compatible_response(messages: List[dict], model_id: str) -> str:
    base_url = os.getenv("OPENAI_COMPAT_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    if not base_url or not api_key:
        raise RuntimeError("OpenAI-compatible provider is not configured")

    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model_id,
        "messages": messages,
        "temperature": 0.2,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Provider HTTP error: {exc.code}") from exc
    except Exception as exc:
        raise RuntimeError(f"Provider request failed: {exc}") from exc

    try:
        return body["choices"][0]["message"]["content"]
    except Exception as exc:
        raise RuntimeError("Provider returned an unexpected response shape") from exc


def generate_assistant_response(chat_id: int, user_message: str, mode: str, model_id: str) -> str:
    history = fetch_messages(chat_id)
    messages = [{"role": "system", "content": SYSTEM_GUIDANCE.get(mode, SYSTEM_GUIDANCE["general"])}]
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message + relevant_workspace_context(chat_id)})

    if model_id.startswith("mock-") or os.getenv("AI_PROVIDER", "mock") == "mock":
        return build_mock_response(mode, user_message, chat_id)

    return openai_compatible_response(messages, model_id)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/bootstrap")
def bootstrap():
    return bootstrap_payload()


@app.get("/api/workspaces")
def list_workspaces():
    return fetch_workspaces()


@app.post("/api/workspaces")
def create_workspace(payload: WorkspaceCreate):
    conn = db()
    cur = conn.execute(
        "INSERT INTO workspaces (name, kind, created_at) VALUES (?, ?, ?)",
        (payload.name, payload.kind, now_iso()),
    )
    conn.commit()
    workspace_id = cur.lastrowid
    conn.close()
    audit("workspace.created", payload.dict())
    return {"id": workspace_id}


@app.get("/api/chats")
def list_chats(workspace_id: Optional[int] = None):
    return fetch_chats(workspace_id)


@app.post("/api/chats")
def create_chat(payload: ChatCreate):
    conn = db()
    cur = conn.execute(
        "INSERT INTO chats (workspace_id, title, created_at) VALUES (?, ?, ?)",
        (payload.workspace_id, payload.title, now_iso()),
    )
    conn.commit()
    chat_id = cur.lastrowid
    conn.close()
    audit("chat.created", payload.dict())
    return {"id": chat_id}


@app.get("/api/chats/{chat_id}")
def get_chat(chat_id: int):
    return {"messages": fetch_messages(chat_id)}


@app.post("/api/chats/{chat_id}/messages")
def send_message(chat_id: int, payload: MessageCreate):
    conn = db()
    chat = conn.execute("SELECT * FROM chats WHERE id = ?", (chat_id,)).fetchone()
    if not chat:
        conn.close()
        raise HTTPException(status_code=404, detail="Chat not found")

    conn.execute(
        "INSERT INTO messages (chat_id, role, content, mode, model_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (chat_id, "user", payload.content, payload.mode, payload.model_id, now_iso()),
    )
    conn.commit()
    conn.close()

    try:
        reply = generate_assistant_response(chat_id, payload.content, payload.mode, payload.model_id)
    except Exception as exc:
        reply = f"Provider error: {exc}\n\nFalling back is recommended unless the provider configuration is fixed."

    conn = db()
    conn.execute(
        "INSERT INTO messages (chat_id, role, content, mode, model_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (chat_id, "assistant", reply, payload.mode, payload.model_id, now_iso()),
    )
    conn.commit()
    conn.close()
    audit("message.sent", payload.dict())
    return {"reply": reply}


@app.get("/api/files")
def list_files(workspace_id: Optional[int] = None):
    return fetch_files(workspace_id)


@app.post("/api/files")
async def upload_file(workspace_id: int = Form(...), file: UploadFile = File(...)):
    raw = await file.read()
    stored = UPLOAD_DIR / f"{datetime.utcnow().timestamp()}_{file.filename}"
    stored.write_bytes(raw)

    extracted_text = None
    if file.content_type and file.content_type.startswith("text"):
        try:
            extracted_text = raw.decode("utf-8", errors="ignore")[:20000]
        except Exception:
            extracted_text = None
    else:
        try:
            extracted_text = raw.decode("utf-8", errors="ignore")[:20000]
        except Exception:
            extracted_text = None

    conn = db()
    cur = conn.execute(
        "INSERT INTO files (workspace_id, filename, content_type, stored_path, extracted_text, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (workspace_id, file.filename, file.content_type, str(stored), extracted_text, now_iso()),
    )
    conn.commit()
    file_id = cur.lastrowid
    conn.close()
    audit("file.uploaded", {"workspace_id": workspace_id, "filename": file.filename})
    return {"id": file_id, "filename": file.filename}


@app.get("/api/prompts")
def list_prompts():
    return fetch_prompts()


@app.post("/api/prompts")
def create_prompt(payload: PromptCreate):
    conn = db()
    cur = conn.execute(
        "INSERT INTO prompts (title, body, scope, created_at) VALUES (?, ?, ?, ?)",
        (payload.title, payload.body, payload.scope, now_iso()),
    )
    conn.commit()
    prompt_id = cur.lastrowid
    conn.close()
    audit("prompt.created", payload.dict())
    return {"id": prompt_id}


@app.get("/api/settings")
def list_settings():
    conn = db()
    rows = conn.execute("SELECT key, value FROM settings ORDER BY key ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/settings")
def upsert_setting(payload: SettingUpdate):
    conn = db()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (payload.key, payload.value),
    )
    conn.commit()
    conn.close()
    audit("setting.updated", payload.dict())
    return {"ok": True}


@app.get("/api/admin/health")
def health():
    return {
        "status": "ok",
        "prototype": True,
        "provider": os.getenv("AI_PROVIDER", "mock"),
        "openai_compatible_enabled": bool(os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_COMPAT_BASE_URL")),
    }
