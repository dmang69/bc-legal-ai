"""Workspaces, chats, messages — ORM-ified port of Phase 1 endpoints."""
from __future__ import annotations

import json
import os
import re
import textwrap
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, File as FastFile, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session as DbSession

from app.config import get_settings
from app.db import get_session
from app.models import Audit, Chat, File, Message, Prompt, Setting, User, Workspace
from app.services.deps import require_user, require_admin, UserPublic

router = APIRouter(prefix="/api", tags=["workspace"])


# --- Schemas -----------------------------------------------------------------

class WorkspaceCreate(BaseModel):
    name: str
    kind: str = "general"


class WorkspaceOut(BaseModel):
    id: int
    name: str
    kind: str


class ChatCreate(BaseModel):
    workspace_id: int
    title: str = "New Chat"


class ChatOut(BaseModel):
    id: int
    workspace_id: int
    title: str


class MessageCreate(BaseModel):
    content: str
    mode: str = "general"
    model_id: str = "mock-general"


class MessageOut(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str
    mode: str
    model_id: str


class PromptCreate(BaseModel):
    title: str
    body: str
    scope: str = "personal"


class PromptOut(BaseModel):
    id: int
    title: str
    body: str
    scope: str


class SettingUpdate(BaseModel):
    key: str
    value: str


class BootstrapOut(BaseModel):
    user: UserPublic
    models: list[dict]
    workspaces: list[WorkspaceOut]
    active_workspace_id: Optional[int]
    chats: list[ChatOut]
    active_chat_id: Optional[int]
    messages: list[MessageOut]
    prompts: list[PromptOut]
    settings: dict


# --- Constants ---------------------------------------------------------------

DEFAULT_MODELS = [
    {"id": "mock-general", "label": "Platform Default", "provider": "mock",
     "modes": ["general", "research"]},
    {"id": "mock-legal", "label": "Legal Counsel", "provider": "mock", "modes": ["legal"]},
    {"id": "mock-code", "label": "Code Copilot", "provider": "mock", "modes": ["code"]},
    {"id": os.getenv("OPENAI_MODEL", "openai-compatible"),
     "label": "OpenAI-Compatible", "provider": "openai-compatible",
     "modes": ["general", "legal", "research", "code"]},
]

SYSTEM_GUIDANCE = {
    "general": "You are a professional enterprise AI assistant. Be useful, "
               "organized, and concise.",
    "legal": ("You are a legal information and drafting support assistant. Never "
              "invent facts. Do not present unsettled law as certain. Separate "
              "FACT, ASSUMPTION, ISSUE, LAW, ANALYSIS, and REMEDY."),
    "research": "You are a research analyst. Break questions into sub-issues, "
                "state uncertainties, and organize findings clearly.",
    "code": "You are a senior engineering copilot. Provide implementation "
            "advice, risks, tests, and clean code suggestions.",
}


# --- Helpers -----------------------------------------------------------------

def _assert_owns_workspace(db: DbSession, workspace_id: int, user_id: int) -> Workspace:
    ws = db.scalar(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.owner_user_id == user_id,
        )
    )
    if not ws:
        raise HTTPException(404, "Workspace not found.")
    return ws


def _assert_owns_chat(db: DbSession, chat_id: int, user_id: int) -> Chat:
    chat = db.scalar(
        select(Chat)
        .join(Workspace, Chat.workspace_id == Workspace.id)
        .where(Chat.id == chat_id, Workspace.owner_user_id == user_id)
    )
    if not chat:
        raise HTTPException(404, "Chat not found.")
    return chat


def _audit(db: DbSession, event_type: str, actor_user_id: Optional[int], payload: dict) -> None:
    db.add(Audit(event_type=event_type, actor_user_id=actor_user_id, payload=payload))
    db.flush()


def _truncate(text: str, length: int = 240) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= length else text[: length - 3] + "..."


def _workspace_context(db: DbSession, chat: Chat) -> str:
    files = db.scalars(
        select(File)
        .where(File.workspace_id == chat.workspace_id)
        .order_by(desc(File.id)).limit(5)
    ).all()
    snippets = []
    for f in files:
        if f.extracted_text and f.extracted_text.strip():
            snippets.append(f"{f.filename}: {_truncate(f.extracted_text)}")
    if not snippets:
        return ""
    return "\n\nWorkspace file snippets:\n- " + "\n- ".join(snippets)


def _build_mock_response(mode: str, user_message: str, ctx: str) -> str:
    if mode == "legal":
        return textwrap.dedent(f"""
            LEGAL INFORMATION / DRAFTING SUPPORT ONLY

            FACT
            - User request: {user_message}

            ASSUMPTIONS
            - Full record and verified authorities not available in this session.
            - Any deadline or legal conclusion must be independently verified.

            NEXT STEP
            - Upload documents, then request a specific work product.
            {ctx}
        """).strip()
    if mode == "research":
        return textwrap.dedent(f"""
            RESEARCH MODE

            Primary Question
            - {user_message}

            Sub-Issues
            1. What exactly needs to be answered?
            2. What sources or authorities are required?
            3. What facts are missing or assumed?
            {ctx}
        """).strip()
    if mode == "code":
        return textwrap.dedent(f"""
            CODE COPILOT MODE

            Task
            - {user_message}

            Plan
            1. Restate the problem in your own words.
            2. Identify inputs, outputs, and invariants.
            3. Sketch the smallest correct implementation.
            {ctx}
        """).strip()
    return textwrap.dedent(f"""
        General assistant reply (mock).

        You asked: {user_message}
        {ctx}
    """).strip()


async def _call_openai_compatible(messages: list[dict], model_id: str) -> str:
    settings = get_settings()
    base_url = settings.OPENAI_COMPAT_BASE_URL.rstrip("/")
    if not base_url or not settings.OPENAI_API_KEY:
        raise HTTPException(400, "OpenAI-compatible provider not configured.")
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.post(
                f"{base_url}/chat/completions",
                json={"model": model_id, "messages": messages},
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            )
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(502, f"Provider error: {e}")
    data = r.json()
    return data["choices"][0]["message"]["content"]


async def _generate_reply(
    db: DbSession, chat: Chat, user_message: str, mode: str, model_id: str,
) -> str:
    settings = get_settings()
    ctx = _workspace_context(db, chat)
    if settings.AI_PROVIDER == "mock" or model_id.startswith("mock-"):
        return _build_mock_response(mode, user_message, ctx)

    history = db.scalars(
        select(Message).where(Message.chat_id == chat.id).order_by(Message.id)
    ).all()
    msgs = [{"role": "system", "content": SYSTEM_GUIDANCE.get(mode, SYSTEM_GUIDANCE["general"]) + ctx}]
    for m in history:
        msgs.append({"role": m.role, "content": m.content})
    msgs.append({"role": "user", "content": user_message})
    return await _call_openai_compatible(msgs, model_id)


# --- Endpoints ---------------------------------------------------------------

@router.get("/bootstrap", response_model=BootstrapOut)
def bootstrap(user: User = Depends(require_user), db: DbSession = Depends(get_session)):
    settings = get_settings()

    workspaces = db.scalars(
        select(Workspace).where(Workspace.owner_user_id == user.id).order_by(Workspace.id)
    ).all()
    active_ws = workspaces[0] if workspaces else None

    chats = []
    active_chat = None
    messages = []
    if active_ws:
        chats = db.scalars(
            select(Chat).where(Chat.workspace_id == active_ws.id).order_by(desc(Chat.id))
        ).all()
        active_chat = chats[0] if chats else None
        if active_chat:
            messages = db.scalars(
                select(Message).where(Message.chat_id == active_chat.id).order_by(Message.id)
            ).all()

    prompts = db.scalars(
        select(Prompt).where(
            (Prompt.scope == "shared") | (Prompt.owner_user_id == user.id)
        ).order_by(desc(Prompt.scope), Prompt.id)
    ).all()

    return BootstrapOut(
        user=UserPublic.from_user(user),
        models=DEFAULT_MODELS,
        workspaces=[WorkspaceOut(id=w.id, name=w.name, kind=w.kind) for w in workspaces],
        active_workspace_id=active_ws.id if active_ws else None,
        chats=[ChatOut(id=c.id, workspace_id=c.workspace_id, title=c.title) for c in chats],
        active_chat_id=active_chat.id if active_chat else None,
        messages=[
            MessageOut(id=m.id, chat_id=m.chat_id, role=m.role, content=m.content,
                       mode=m.mode, model_id=m.model_id)
            for m in messages
        ],
        prompts=[PromptOut(id=p.id, title=p.title, body=p.body, scope=p.scope) for p in prompts],
        settings={
            "provider": settings.AI_PROVIDER,
            "openai_compatible_enabled": bool(settings.OPENAI_API_KEY and settings.OPENAI_COMPAT_BASE_URL),
        },
    )


@router.get("/workspaces", response_model=list[WorkspaceOut])
def list_workspaces(user: User = Depends(require_user), db: DbSession = Depends(get_session)):
    rows = db.scalars(
        select(Workspace).where(Workspace.owner_user_id == user.id).order_by(Workspace.id)
    ).all()
    return [WorkspaceOut(id=w.id, name=w.name, kind=w.kind) for w in rows]


@router.post("/workspaces", response_model=WorkspaceOut, status_code=201)
def create_workspace(
    payload: WorkspaceCreate,
    user: User = Depends(require_user),
    db: DbSession = Depends(get_session),
):
    ws = Workspace(owner_user_id=user.id, name=payload.name, kind=payload.kind)
    db.add(ws)
    db.flush()
    _audit(db, "workspace.create", user.id, {"workspace_id": ws.id, "name": ws.name})
    return WorkspaceOut(id=ws.id, name=ws.name, kind=ws.kind)


@router.get("/chats", response_model=list[ChatOut])
def list_chats(
    workspace_id: Optional[int] = None,
    user: User = Depends(require_user),
    db: DbSession = Depends(get_session),
):
    q = select(Chat).join(Workspace, Chat.workspace_id == Workspace.id).where(
        Workspace.owner_user_id == user.id
    )
    if workspace_id is not None:
        _assert_owns_workspace(db, workspace_id, user.id)
        q = q.where(Chat.workspace_id == workspace_id)
    rows = db.scalars(q.order_by(desc(Chat.id))).all()
    return [ChatOut(id=c.id, workspace_id=c.workspace_id, title=c.title) for c in rows]


@router.post("/chats", response_model=ChatOut, status_code=201)
def create_chat(
    payload: ChatCreate,
    user: User = Depends(require_user),
    db: DbSession = Depends(get_session),
):
    _assert_owns_workspace(db, payload.workspace_id, user.id)
    chat = Chat(workspace_id=payload.workspace_id, title=payload.title)
    db.add(chat)
    db.flush()
    _audit(db, "chat.create", user.id, {"chat_id": chat.id})
    return ChatOut(id=chat.id, workspace_id=chat.workspace_id, title=chat.title)


@router.get("/chats/{chat_id}")
def get_chat(
    chat_id: int,
    user: User = Depends(require_user),
    db: DbSession = Depends(get_session),
):
    chat = _assert_owns_chat(db, chat_id, user.id)
    messages = db.scalars(
        select(Message).where(Message.chat_id == chat_id).order_by(Message.id)
    ).all()
    return {
        "chat": ChatOut(id=chat.id, workspace_id=chat.workspace_id, title=chat.title),
        "messages": [
            MessageOut(id=m.id, chat_id=m.chat_id, role=m.role, content=m.content,
                       mode=m.mode, model_id=m.model_id)
            for m in messages
        ],
    }


@router.post("/chats/{chat_id}/messages")
async def send_message(
    chat_id: int,
    payload: MessageCreate,
    user: User = Depends(require_user),
    db: DbSession = Depends(get_session),
):
    chat = _assert_owns_chat(db, chat_id, user.id)

    db.add(Message(
        chat_id=chat_id, role="user", content=payload.content,
        mode=payload.mode, model_id=payload.model_id,
    ))
    db.flush()

    reply = await _generate_reply(db, chat, payload.content, payload.mode, payload.model_id)

    db.add(Message(
        chat_id=chat_id, role="assistant", content=reply,
        mode=payload.mode, model_id=payload.model_id,
    ))
    _audit(db, "chat.message", user.id, {"chat_id": chat_id, "mode": payload.mode})
    return {"reply": reply}


# --- Files -------------------------------------------------------------------

@router.get("/files")
def list_files(
    workspace_id: Optional[int] = None,
    user: User = Depends(require_user),
    db: DbSession = Depends(get_session),
):
    q = select(File).join(Workspace, File.workspace_id == Workspace.id).where(
        Workspace.owner_user_id == user.id
    )
    if workspace_id is not None:
        _assert_owns_workspace(db, workspace_id, user.id)
        q = q.where(File.workspace_id == workspace_id)
    rows = db.scalars(q.order_by(desc(File.id))).all()
    return [
        {"id": f.id, "workspace_id": f.workspace_id, "filename": f.filename,
         "content_type": f.content_type, "byte_size": f.byte_size}
        for f in rows
    ]


@router.post("/files", status_code=201)
async def upload_file(
    workspace_id: int = Form(...),
    file: UploadFile = FastFile(...),
    user: User = Depends(require_user),
    db: DbSession = Depends(get_session),
):
    settings = get_settings()
    _assert_owns_workspace(db, workspace_id, user.id)

    data = await file.read(settings.MAX_UPLOAD_BYTES + 1)
    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"File exceeds {settings.MAX_UPLOAD_BYTES // (1024*1024)} MiB.")

    safe_name = Path(file.filename or "unnamed").name
    if not safe_name:
        raise HTTPException(400, "Invalid filename.")

    upload_dir = Path(settings.UPLOAD_DIR) / f"u{user.id}"
    upload_dir.mkdir(parents=True, exist_ok=True)
    from datetime import datetime, timezone
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    dest = upload_dir / f"{stamp}-{safe_name}"
    dest.write_bytes(data)

    extracted = ""
    if (file.content_type or "").startswith("text/"):
        try:
            extracted = data.decode("utf-8", errors="replace")[:20000]
        except Exception:
            extracted = ""

    row = File(
        workspace_id=workspace_id, filename=safe_name,
        content_type=file.content_type, stored_path=str(dest),
        extracted_text=extracted, byte_size=len(data),
    )
    db.add(row)
    db.flush()
    _audit(db, "file.upload", user.id, {"file_id": row.id, "bytes": len(data)})
    return {"id": row.id, "filename": safe_name, "content_type": file.content_type,
            "byte_size": len(data)}


# --- Prompts / Settings / Admin ---------------------------------------------

@router.get("/prompts", response_model=list[PromptOut])
def list_prompts(user: User = Depends(require_user), db: DbSession = Depends(get_session)):
    rows = db.scalars(
        select(Prompt).where(
            (Prompt.scope == "shared") | (Prompt.owner_user_id == user.id)
        ).order_by(desc(Prompt.scope), Prompt.id)
    ).all()
    return [PromptOut(id=p.id, title=p.title, body=p.body, scope=p.scope) for p in rows]


@router.post("/prompts", response_model=PromptOut, status_code=201)
def create_prompt(
    payload: PromptCreate,
    user: User = Depends(require_user),
    db: DbSession = Depends(get_session),
):
    if payload.scope not in ("personal", "shared"):
        raise HTTPException(400, "scope must be 'personal' or 'shared'.")
    if payload.scope == "shared" and user.role != "admin":
        raise HTTPException(403, "Admin required to create shared prompts.")

    p = Prompt(
        owner_user_id=user.id if payload.scope == "personal" else None,
        title=payload.title, body=payload.body, scope=payload.scope,
    )
    db.add(p)
    db.flush()
    _audit(db, "prompt.create", user.id, {"prompt_id": p.id, "scope": p.scope})
    return PromptOut(id=p.id, title=p.title, body=p.body, scope=p.scope)


@router.get("/settings")
def list_settings(user: User = Depends(require_user), db: DbSession = Depends(get_session)):
    rows = db.scalars(select(Setting).where(Setting.user_id == user.id)).all()
    return {r.key: r.value for r in rows}


@router.post("/settings")
def upsert_setting(
    payload: SettingUpdate,
    user: User = Depends(require_user),
    db: DbSession = Depends(get_session),
):
    existing = db.get(Setting, (user.id, payload.key))
    if existing:
        existing.value = payload.value
    else:
        db.add(Setting(user_id=user.id, key=payload.key, value=payload.value))
    db.flush()
    return {"key": payload.key, "value": payload.value}


@router.get("/admin/health")
def admin_health(_user: User = Depends(require_admin), db: DbSession = Depends(get_session)):
    counts = {}
    for m in [User, Workspace, Chat, Message, File, Prompt, Audit]:
        counts[m.__tablename__] = db.scalar(select(func.count()).select_from(m)) or 0
    return {"ok": True, "counts": counts}
