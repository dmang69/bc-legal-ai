"""Persistent workspace conversations and messages."""

from __future__ import annotations

import json
import uuid
from typing import Any

from backend.api.public_demo import reject_if_public_demo
from backend.db import get_connection, init_db
from backend.identity import AuthError, UserInfo, get_identity_service

_ALLOWED_MODES = {"general", "matter", "document", "research", "drafting", "agent"}


def _conversation_id() -> str:
    return f"conv_{uuid.uuid4().hex[:16]}"


def _message_id() -> str:
    return f"wmsg_{uuid.uuid4().hex[:16]}"


def create_conversation(
    *,
    user: UserInfo,
    matter_id: str = "",
    title: str = "Workspace conversation",
    mode: str = "general",
) -> dict[str, Any]:
    reject_if_public_demo("persistent workspace conversation")
    init_db()
    mode = mode.strip().lower() or "general"
    if mode not in _ALLOWED_MODES:
        raise ValueError("Unsupported workspace mode")
    if matter_id and not get_identity_service().can_access_matter(user, matter_id):
        raise AuthError("Matter access denied")
    cid = _conversation_id()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO workspace_conversations
            (conversation_id, matter_id, org_id, title, mode, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (cid, matter_id, user.org_id, title or "Workspace conversation", mode, user.user_id),
        )
    return get_conversation(user=user, conversation_id=cid)


def get_conversation(*, user: UserInfo, conversation_id: str) -> dict[str, Any]:
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM workspace_conversations WHERE conversation_id = ?",
            (conversation_id,),
        ).fetchone()
        if not row:
            raise AuthError("Conversation not found")
        if row["org_id"] != user.org_id:
            raise AuthError("Conversation access denied")
        if row["matter_id"] and not get_identity_service().can_access_matter(user, row["matter_id"]):
            raise AuthError("Matter access denied")
        messages = conn.execute(
            """
            SELECT * FROM workspace_messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
            """,
            (conversation_id,),
        ).fetchall()
    return {
        "conversation_id": row["conversation_id"],
        "matter_id": row["matter_id"],
        "org_id": row["org_id"],
        "title": row["title"],
        "mode": row["mode"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "messages": [_message_to_dict(message) for message in messages],
    }


def list_conversations(*, user: UserInfo, matter_id: str = "") -> list[dict[str, Any]]:
    init_db()
    params: tuple[Any, ...]
    sql = """
        SELECT conversation_id, matter_id, org_id, title, mode, created_by, created_at, updated_at
        FROM workspace_conversations
        WHERE org_id = ?
    """
    params = (user.org_id,)
    if matter_id:
        if not get_identity_service().can_access_matter(user, matter_id):
            raise AuthError("Matter access denied")
        sql += " AND matter_id = ?"
        params = (user.org_id, matter_id)
    sql += " ORDER BY updated_at DESC"
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def add_message(
    *,
    user: UserInfo,
    conversation_id: str,
    author: str,
    body: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    reject_if_public_demo("persistent workspace message")
    init_db()
    conversation = get_conversation(user=user, conversation_id=conversation_id)
    if author not in {"user", "assistant", "agent", "system"}:
        raise ValueError("Unsupported message author")
    if not body.strip():
        raise ValueError("Message body required")
    mid = _message_id()
    metadata = metadata or {}
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO workspace_messages
            (message_id, conversation_id, matter_id, author, body, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                mid,
                conversation_id,
                conversation["matter_id"],
                author,
                body.strip(),
                json.dumps(metadata),
            ),
        )
        conn.execute(
            """
            UPDATE workspace_conversations
            SET updated_at = datetime('now')
            WHERE conversation_id = ?
            """,
            (conversation_id,),
        )
        row = conn.execute(
            "SELECT * FROM workspace_messages WHERE message_id = ?",
            (mid,),
        ).fetchone()
    return _message_to_dict(row)


def _message_to_dict(row: Any) -> dict[str, Any]:
    item = dict(row)
    item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
    return item
