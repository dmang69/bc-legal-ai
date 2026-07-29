"""
Enterprise AI Platform — Multi-Model Workspace Backend
======================================================
Features:
- ChatGPT-style conversation UX
- Claude-style long-form reasoning + document workspaces
- Copilot-style code mode
- Monica-style prompt library and multi-provider access
- Kimi-style research mode with long-context analysis
- Legal-grade matter, evidence, drafting, and review workflows

Architecture:
- FastAPI + Python backend
- SQLite (dev) / PostgreSQL (prod) via raw SQL adapter
- Pluggable model gateway: mock, OpenAI-compatible, Anthropic-compatible
- Jinja2 templated UI with static assets
- Audit trail for all operations

Setup:
  pip install -r requirements.txt
  uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import textwrap
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Paths & Configuration
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "platform.db"
UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

UPLOAD_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="Enterprise AI Platform",
    version="0.6.0",
    description=(
        "Multi-model enterprise AI workspace: chat, legal, research, code. "
        "Not a lawyer. Not legal advice. Human supervision required."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------
class WorkspaceCreate(BaseModel):
    name: str
    kind: str = "general"

class ChatCreate(BaseModel):
    workspace_id: int
    title: str = "New Chat"

class MessageCreate(BaseModel):
    content: str
    mode: str = "general"
    model_id: str = "mock-general"

class PromptCreate(BaseModel):
    title: str
    body: str
    scope: str = "personal"

class SettingUpdate(BaseModel):
    key: str
    value: str

# ---------------------------------------------------------------------------
# Default Data
# ---------------------------------------------------------------------------
DEFAULT_MODELS = [
    {"id": "mock-general", "label": "Platform Default", "provider": "mock", "modes": ["general", "research", "legal"]},
    {"id": "mock-legal", "label": "Legal Counsel", "provider": "mock", "modes": ["legal"]},
    {"id": "mock-code", "label": "Code Copilot", "provider": "mock", "modes": ["code"]},
    {"id": "openai-compatible", "label": "OpenAI-Compatible", "provider": "openai", "modes": ["general", "legal", "research", "code"]},
    {"id": "anthropic-compatible", "label": "Anthropic-Compatible", "provider": "anthropic", "modes": ["general", "legal", "research"]},
    {"id": "local-model", "label": "Local Model (Self-Hosted)", "provider": "local", "modes": ["general", "code"]},
]

DEFAULT_PROMPTS: list[tuple[str, str, str]] = [
    ("Legal Issue Matrix", "Organize the problem into: Facts, Assumptions, Issues, Governing Law, Evidence Gaps, Counterarguments, Requested Remedy.", "team"),
    ("Case Chronology", "Turn the record into a clean chronology with: Date, Event, Source, Why It Matters.", "team"),
    ("Code Review Checklist", "Review the code for: Correctness, Security, Maintainability, Performance, Testing Gaps, Documentation.", "team"),
    ("Research Memo Structure", "Produce a research memo with: Question, Summary, Background, Analysis, Sub-Issues, Conclusions, Open Questions.", "team"),
    ("Draft Petition Outline", "Draft a Form 66/67 outline with: Caption, Orders Sought, Grounds, Material Facts, Legal Basis, Signature Block.", "team"),
    ("Evidence Summary", "Summarize the evidence with: Document ID, Date, Type, Key Facts, Relevance, Admissibility Concerns, Privilege Status.", "team"),
    ("Fail-Closed Analysis", "Analyze with explicit separation: Verified Facts, Assumptions, Uncertainties, Legal Tests, Recommended Next Steps.", "team"),
]

SYSTEM_GUIDANCE: dict[str, str] = {
    "general": "You are a professional enterprise AI assistant. Be useful, organized, and concise. Support multi-step reasoning and refer to workspace files when available.",
    "legal": (
        "You are a legal information and drafting support assistant. Never invent facts. "
        "Do not present unsettled law as certain. Separate FACT, ASSUMPTION, ISSUE, LAW, ANALYSIS, and REMEDY. "
        "Output suitable for counsel refinement before filing.\n\n"
        "Structure:\n"
        "FACT\n- Verified facts from the record\n\n"
        "ASSUMPTIONS / MISSING VERIFICATION\n- What we don't know or need to confirm\n\n"
        "ISSUE FRAME\n- Governing forum, legislation, deadlines, evidentiary record\n\n"
        "WORKING ANALYSIS\n- Apply law to facts; flag uncertainties\n\n"
        "DRAFTING OUTPUT\n- Chronology, issue list, affidavit draft, submission outline, petition skeleton\n\n"
        "RECOMMENDED NEXT STEP\n- What to verify, upload, or request next\n\n"
        "DISCLAIMER: This is not legal advice. Human review required before any filing or reliance."
    ),
    "research": (
        "You are a research analyst. Break questions into sub-issues, state uncertainties, and organize findings clearly.\n\n"
        "Structure:\n"
        "Primary Question\n"
        "Sub-Issues\n"
        "Research Plan\n"
        "Findings by Issue\n"
        "Open Questions / Uncertainties\n"
        "Recommended Next Steps"
    ),
    "code": (
        "You are a senior engineering copilot. Provide implementation advice, risks, tests, and clean code suggestions.\n\n"
        "Structure:\n"
        "Understanding of Request\n"
        "Architecture / Design Considerations\n"
        "Implementation Plan\n"
        "Code Snippets (if applicable)\n"
        "Testing Strategy\n"
        "Risks / Gotchas\n"
        "Alternative Approaches"
    ),
}

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db() -> None:
    conn = db()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS workspaces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            kind TEXT NOT NULL DEFAULT 'general',
            description TEXT NOT NULL DEFAULT '',
            tags TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workspace_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            pinned INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            mode TEXT NOT NULL DEFAULT 'general',
            model_id TEXT NOT NULL DEFAULT 'mock-general',
            metadata TEXT NOT NULL DEFAULT '{}',
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
            scope TEXT NOT NULL DEFAULT 'personal',
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
        CREATE TABLE IF NOT EXISTS artifacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            kind TEXT NOT NULL DEFAULT 'note',
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()

    existing = cur.execute("SELECT COUNT(*) AS c FROM prompts").fetchone()["c"]
    if existing == 0 and DEFAULT_PROMPTS:
        cur.executemany(
            "INSERT INTO prompts (title, body, scope, created_at) VALUES (?, ?, ?, ?)",
            [(t, b, s, now_iso()) for t, b, s in DEFAULT_PROMPTS],
        )
        conn.commit()

    existing_ws = cur.execute("SELECT COUNT(*) AS c FROM workspaces").fetchone()["c"]
    if existing_ws == 0:
        cur.execute(
            "INSERT INTO workspaces (name, kind, description, created_at) VALUES (?, ?, ?, ?)",
            ("Default Workspace", "general", "Enterprise AI workspace — supports General, Legal, Research, and Code modes.", now_iso()),
        )
        wid = cur.lastrowid
        cur.execute(
            "INSERT INTO chats (workspace_id, title, created_at) VALUES (?, ?, ?)",
            (wid, "Welcome to Enterprise AI Platform", now_iso()),
        )
        cid = cur.lastrowid
        welcome_msg = (
            "# Welcome to Enterprise AI Platform\n\n"
            "## Features\n\n"
            "### 💬 General Assistant\n"
            "Everyday chat, writing, brainstorming — ChatGPT-style conversation.\n\n"
            "### ⚖️ Legal Counsel Mode\n"
            "Structured legal analysis: Facts → Issues → Law → Analysis → Remedy.\n\n"
            "### 🔍 Research Mode\n"
            "Deep research with issue trees, contradiction detection, and long-context synthesis.\n\n"
            "### 💻 Code Copilot Mode\n"
            "Code generation, debugging, architecture review, and refactoring.\n\n"
            "### 📋 Prompt Library\n"
            "Reusable prompt templates for common workflows.\n\n"
            "### 📁 Workspace Files\n"
            "Upload documents and reference them in conversations.\n\n"
            "### 🔄 Multi-Model Support\n"
            "Switch between mock, OpenAI-compatible, and Anthropic-compatible providers.\n\n"
            "## Getting Started\n"
            "1. Select a mode using the mode chips\n"
            "2. Choose a model from the dropdown\n"
            "3. Ask a question or request a task\n"
            "4. Attach files for workspace context\n"
            "5. Save prompts to reuse later\n\n"
            "*This platform is not a lawyer. Not legal advice. Human supervision required.*"
        )
        cur.execute(
            "INSERT INTO messages (chat_id, role, content, mode, model_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (cid, "assistant", welcome_msg, "general", "mock-general", now_iso()),
        )
        conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------
def audit(event_type: str, payload: dict) -> None:
    conn = db()
    conn.execute(
        "INSERT INTO audits (event_type, payload, created_at) VALUES (?, ?, ?)",
        (event_type, json.dumps(payload), now_iso()),
    )
    conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def truncate(text: str, length: int = 180) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= length else text[: length - 3] + "..."

def fetch_messages(chat_id: int) -> list[dict]:
    conn = db()
    rows = conn.execute("SELECT * FROM messages WHERE chat_id = ? ORDER BY id ASC", (chat_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def relevant_workspace_context(chat_id: int) -> str:
    conn = db()
    chat = conn.execute("SELECT * FROM chats WHERE id = ?", (chat_id,)).fetchone()
    if not chat:
        conn.close()
        return ""
    files = conn.execute(
        "SELECT filename, extracted_text FROM files WHERE workspace_id = ? ORDER BY id DESC LIMIT 10",
        (chat["workspace_id"],),
    ).fetchall()
    conn.close()
    snippets = []
    for row in files:
        text = row["extracted_text"] or ""
        if text.strip():
            snippets.append(f"- **{row['filename']}**: {truncate(text, 240)}")
    if not snippets:
        return ""
    return "\n\n### Relevant Workspace Files\n" + "\n".join(snippets)

# ---------------------------------------------------------------------------
# AI Response Generation
# ---------------------------------------------------------------------------
def build_mock_response(mode: str, user_message: str, chat_id: int) -> str:
    ctx = relevant_workspace_context(chat_id)
    if mode == "legal":
        return textwrap.dedent(f"""\
## LEGAL ANALYSIS — STRUCTURED OUTPUT

### FACT
- User request: {user_message[:200]}

### ASSUMPTIONS / MISSING VERIFICATION
- Full record, governing documents, and verified authorities not available
- Any filing, legal conclusion, or deadline must be independently checked
- Jurisdiction, procedural rules, and applicable legislation require confirmation

### ISSUE FRAME
- Identify governing forum, legislation, deadlines, and evidentiary record
- Separate proven facts from allegations and strategy from evidence
- Confirm limitation periods, filing deadlines, and available remedies

### WORKING ANALYSIS
- Extract a chronology and issue matrix from available documents
- Map facts to legal tests and identify gaps
- Flag procedural requirements and potential obstacles

### DRAFTING OUTPUT AVAILABLE
- Chronology of events
- Issue list / legal test matrix
- Affidavit draft outline
- Submission / factum skeleton
- Petition (Form 66/67) outline
- Witness plan
- Evidence chart

### RECOMMENDED NEXT STEPS
1. Upload relevant notices, agreements, decisions, correspondence
2. Specify jurisdiction and court/tribunal
3. Request specific work product (e.g., \"draft petition\", \"build JR grounds table\")
4. Route for human review before any filing{ctx}
""").strip()
    elif mode == "research":
        return textwrap.dedent(f"""\
## RESEARCH MODE — STRUCTURED ANALYSIS

### Primary Question
{user_message[:200]}

### Sub-Issues
1. What exactly needs to be answered?
2. What sources or authorities are required?
3. What facts are missing or assumed?
4. What competing interpretations or risks exist?
5. What would change the answer?

### Research Plan
- Define jurisdiction and date range
- Identify statute / rule / policy / case sources
- Distinguish binding vs persuasive authorities
- Extract contradictions and unresolved questions
- Produce structured memo with citation flags

### Preliminary Findings
- *Research in progress — upload source documents for detailed analysis*
- Key concepts and legal tests need to be identified from the query
- Cross-reference with BC Laws, CanLII, and official sources required

### Open Questions
- What is the specific legal test or standard?
- What is the relevant time period?
- What jurisdiction(s) apply?
- Are there procedural requirements that affect the analysis?{ctx}
""").strip()
    elif mode == "code":
        return textwrap.dedent(f"""\
## CODE COPILOT — ENGINEERING ANALYSIS

### Request Understanding
{user_message[:200]}

### Architecture Considerations
- What stack and runtime are involved?
- What interfaces and data models are needed?
- Are there existing patterns or conventions to follow?
- What security and performance requirements exist?

### Implementation Plan
1. Define interfaces and data models first
2. Implement core business logic
3. Add integration points (adapters, providers)
4. Write tests for core workflows and edge cases
5. Document API and usage

### Code Quality Checklist
- [ ] Correctness: Does it handle edge cases?
- [ ] Security: Are inputs validated? Is authentication required?
- [ ] Performance: Are there N+1 queries or bottlenecks?
- [ ] Maintainability: Is the code well-structured and documented?
- [ ] Testability: Can core logic be tested without infrastructure?
- [ ] Observability: Are there logs, metrics, or traces?

### Suggested Approach
*Share code or a repository summary for a detailed implementation review.*{ctx}
""").strip()
    else:
        return textwrap.dedent(f"""\
## General Assistant

### I understood your request as:
{user_message[:200]}

### Suggested Approach
1. Clarify the specific deliverable you want
2. Attach relevant files for workspace context
3. Switch mode if you need legal, research, or code-specific output
4. Use the prompt library for recurring workflows

### Available Capabilities
- 💬 **General**: Chat, writing, brainstorming
- ⚖️ **Legal**: Structured legal analysis, drafting, evidence
- 🔍 **Research**: Deep research with issue trees
- 💻 **Code**: Code generation, review, architecture
- 📁 **Files**: Upload and reference documents
- 📋 **Prompts**: Reusable templates
- 🔄 **Multi-Model**: Mock, OpenAI, Anthropic

### Quick Actions
- Ask a legal question in ⚖️ Legal mode
- Request code review in 💻 Code mode
- Upload a document and ask for analysis
- Create a reusable prompt template{ctx}
""").strip()

def openai_compatible_response(messages: list[dict], model_id: str) -> str:
    base_url = os.getenv("OPENAI_COMPAT_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    if not base_url or not api_key:
        raise RuntimeError("OpenAI-compatible provider not configured. Set OPENAI_COMPAT_BASE_URL and OPENAI_API_KEY.")
    url = base_url.rstrip("/") + "/chat/completions"
    payload: dict[str, Any] = {
        "model": model_id,
        "messages": messages,
        "temperature": float(os.getenv("AI_TEMPERATURE", "0.3")),
        "max_tokens": int(os.getenv("AI_MAX_TOKENS", "4096")),
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"OpenAI-compatible HTTP error: {exc.code} {exc.reason}") from exc
    except Exception as exc:
        raise RuntimeError(f"OpenAI-compatible request failed: {exc}") from exc
    try:
        return body["choices"][0]["message"]["content"]
    except Exception as exc:
        raise RuntimeError("OpenAI returned unexpected response shape") from exc

def anthropic_compatible_response(messages: list[dict], model_id: str) -> str:
    base_url = os.getenv("ANTHROPIC_COMPAT_BASE_URL")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not base_url or not api_key:
        raise RuntimeError("Anthropic-compatible provider not configured.")
    system_msg = None
    converted: list[dict[str, str]] = []
    for m in messages:
        if m["role"] == "system":
            system_msg = m["content"]
        else:
            converted.append({"role": m["role"], "content": m["content"]})
    url = base_url.rstrip("/") + "/messages"
    payload: dict[str, Any] = {"model": model_id, "messages": converted, "max_tokens": int(os.getenv("AI_MAX_TOKENS", "4096"))}
    if system_msg:
        payload["system"] = system_msg
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-api-key": api_key, "anthropic-version": "2023-06-01"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Anthropic HTTP error: {exc.code} {exc.reason}") from exc
    except Exception as exc:
        raise RuntimeError(f"Anthropic request failed: {exc}") from exc
    try:
        return body["content"][0]["text"]
    except Exception as exc:
        raise RuntimeError("Anthropic returned unexpected response shape") from exc

def generate_assistant_response(chat_id: int, user_message: str, mode: str, model_id: str) -> str:
    history = fetch_messages(chat_id)
    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_GUIDANCE.get(mode, SYSTEM_GUIDANCE["general"])}
    ]
    for msg in history[-20:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message + relevant_workspace_context(chat_id)})
    provider = os.getenv("AI_PROVIDER", "mock")
    if provider == "anthropic" and model_id.startswith("claude"):
        return anthropic_compatible_response(messages, model_id)
    elif provider in ("openai", "openai-compatible"):
        return openai_compatible_response(messages, model_id)
    else:
        return build_mock_response(mode, user_message, chat_id)

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
def bootstrap_payload() -> dict:
    conn = db()
    workspaces = [dict(r) for r in conn.execute("SELECT * FROM workspaces ORDER BY id DESC").fetchall()]
    active_workspace_id = workspaces[0]["id"] if workspaces else None
    chats: list[dict] = []
    active_chat_id = None
    if active_workspace_id:
        chats = [dict(r) for r in conn.execute("SELECT * FROM chats WHERE workspace_id = ? ORDER BY id DESC", (active_workspace_id,)).fetchall()]
        active_chat_id = chats[0]["id"] if chats else None
    messages: list[dict] = []
    if active_chat_id:
        messages = [dict(r) for r in conn.execute("SELECT * FROM messages WHERE chat_id = ? ORDER BY id ASC", (active_chat_id,)).fetchall()]
    files: list[dict] = []
    if active_workspace_id:
        files = [dict(r) for r in conn.execute("SELECT * FROM files WHERE workspace_id = ? ORDER BY id DESC", (active_workspace_id,)).fetchall()]
    prompts = [dict(r) for r in conn.execute("SELECT * FROM prompts ORDER BY id DESC").fetchall()]
    conn.close()
    return {
        "models": DEFAULT_MODELS,
        "workspaces": workspaces,
        "active_workspace_id": active_workspace_id,
        "chats": chats,
        "active_chat_id": active_chat_id,
        "messages": messages,
        "files": files,
        "prompts": prompts,
        "settings": {
            "provider": os.getenv("AI_PROVIDER", "mock"),
            "temperature": os.getenv("AI_TEMPERATURE", "0.3"),
            "max_tokens": os.getenv("AI_MAX_TOKENS", "4096"),
            "openai_enabled": bool(os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_COMPAT_BASE_URL")),
            "anthropic_enabled": bool(os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_COMPAT_BASE_URL")),
        },
    }

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
def startup() -> None:
    init_db()

# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

# ---------------------------------------------------------------------------
# API — Bootstrap
# ---------------------------------------------------------------------------
@app.get("/api/bootstrap")
def bootstrap():
    return bootstrap_payload()

# ---------------------------------------------------------------------------
# API — Workspaces
# ---------------------------------------------------------------------------
@app.get("/api/workspaces")
def list_workspaces():
    conn = db()
    rows = conn.execute("SELECT * FROM workspaces ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/workspaces")
def create_workspace(payload: WorkspaceCreate):
    conn = db()
    cur = conn.execute(
        "INSERT INTO workspaces (name, kind, created_at) VALUES (?, ?, ?)",
        (payload.name, payload.kind, now_iso()),
    )
    conn.commit()
    wid = cur.lastrowid
    cid = conn.execute(
        "INSERT INTO chats (workspace_id, title, created_at) VALUES (?, ?, ?)",
        (wid, "New Chat", now_iso()),
    ).lastrowid
    conn.commit()
    conn.execute(
        "INSERT INTO messages (chat_id, role, content, mode, model_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (cid, "assistant", f"Workspace **{payload.name}** created. Select a mode to begin.", "general", "mock-general", now_iso()),
    )
    conn.commit()
    conn.close()
    audit("workspace.created", payload.dict())
    return {"id": wid, "default_chat_id": cid}

@app.delete("/api/workspaces/{workspace_id}")
def delete_workspace(workspace_id: int):
    conn = db()
    conn.execute("DELETE FROM files WHERE workspace_id = ?", (workspace_id,))
    conn.execute("DELETE FROM artifacts WHERE chat_id IN (SELECT id FROM chats WHERE workspace_id = ?)", (workspace_id,))
    conn.execute("DELETE FROM messages WHERE chat_id IN (SELECT id FROM chats WHERE workspace_id = ?)", (workspace_id,))
    conn.execute("DELETE FROM chats WHERE workspace_id = ?", (workspace_id,))
    conn.execute("DELETE FROM workspaces WHERE id = ?", (workspace_id,))
    conn.commit()
    conn.close()
    audit("workspace.deleted", {"workspace_id": workspace_id})
    return {"ok": True}

# ---------------------------------------------------------------------------
# API — Chats
# ---------------------------------------------------------------------------
@app.get("/api/chats")
def list_chats(workspace_id: Optional[int] = None):
    conn = db()
    if workspace_id:
        rows = conn.execute("SELECT * FROM chats WHERE workspace_id = ? ORDER BY id DESC", (workspace_id,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM chats ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/chats")
def create_chat(payload: ChatCreate):
    conn = db()
    cur = conn.execute(
        "INSERT INTO chats (workspace_id, title, created_at) VALUES (?, ?, ?)",
        (payload.workspace_id, payload.title, now_iso()),
    )
    conn.commit()
    cid = cur.lastrowid
    conn.execute(
        "INSERT INTO messages (chat_id, role, content, mode, model_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (cid, "assistant", f"## {payload.title}\n\nSelect a mode and model, then ask your question.", "general", "mock-general", now_iso()),
