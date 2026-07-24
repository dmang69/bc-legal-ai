"""
Conversational legal workspace (scaffold).

Persists chats and messages; generates structured assistant replies with
citations/actions. Full LLM routing is pluggable — default is a
deterministic BC-legal support orchestrator (not autonomous advice).
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional

from backend.db import get_connection, init_db
from backend.db.helpers import compat_schema_ddl, now_iso, wrap_timestamp_defaults
from backend.identity import AuthError, UserInfo, get_identity_service
from backend.platform.citations import verify_citation
from backend.platform.model_providers import ChatModelRequest, get_model_provider_registry

_CHAT_DDL = """
CREATE TABLE IF NOT EXISTS conversations (
  conversation_id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  title TEXT NOT NULL DEFAULT 'New chat',
  chat_type TEXT NOT NULL DEFAULT 'general',
  matter_id TEXT,
  model_mode TEXT NOT NULL DEFAULT 'balanced',
  specialist TEXT NOT NULL DEFAULT 'bc_legal_associate',
  archived INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT '',
  updated_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS chat_messages (
  message_id TEXT PRIMARY KEY,
  conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  meta_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT ''
);
"""

SPECIALISTS = [
    {"id": "bc_legal_associate", "name": "BC Legal Associate", "description": "General BC legal workspace triage and supervised drafting.", "capabilities": ["chat", "legal_triage", "drafting", "citations"]},
    {"id": "rtb_specialist", "name": "RTB Specialist", "description": "Residential tenancy issue spotting, RTB process, and evidence organization.", "capabilities": ["tenancy", "rtb", "evidence", "deadlines"]},
    {"id": "jr_counsel", "name": "Judicial Review Counsel", "description": "Judicial review grounds, record review, statutory reasonableness, and petition structure.", "capabilities": ["judicial_review", "vavilov", "drafting", "record_review"]},
    {"id": "statutory_interpreter", "name": "Statutory Interpreter", "description": "Text, context, scheme, purpose, consequences, and Vavilov statutory constraints.", "capabilities": ["statutory_interpretation", "scheme_analysis", "purpose_analysis"]},
    {"id": "legal_terminology", "name": "Legal Terminology Translator", "description": "Terminology cleanup, plain-language conversion, and doctrine distinction policing.", "capabilities": ["terminology", "plain_language", "draft_cleanup"]},
    {"id": "evidence_analyst", "name": "Evidence Analyst", "description": "Evidence matrix, gaps, chronology, propositions, and source-linking.", "capabilities": ["evidence", "chronology", "gap_analysis"]},
    {"id": "citation_clerk", "name": "Citation Clerk", "description": "Fail-closed citation triage and authority verification workflow.", "capabilities": ["citations", "authority_check", "court_ready_gate"]},
    {"id": "procedural_clerk", "name": "Procedural Clerk", "description": "Procedure checklists, filing steps, service, and forum-sensitive tasks.", "capabilities": ["procedure", "service", "forms"]},
    {"id": "deadline_clerk", "name": "Deadline Clerk", "description": "Provisional deadline collection and human-confirmation workflow.", "capabilities": ["deadlines", "jr_clock", "limitation_triage"]},
    {"id": "affidavit_drafter", "name": "Affidavit Drafter", "description": "Fact/evidence-separated affidavit outline support.", "capabilities": ["affidavits", "evidence", "drafting"]},
    {"id": "boa_builder", "name": "Book of Authorities Builder", "description": "Authority extraction, verification plan, and BOA assembly workflow.", "capabilities": ["authorities", "boa", "pinpoints"]},
    {"id": "cross_exam_planner", "name": "Cross-Examination Planner", "description": "Issue-driven cross-examination topics and impeachment planning.", "capabilities": ["cross_examination", "witnesses", "impeachment"]},
    {"id": "devils_advocate", "name": "Devil's Advocate", "description": "Opposing-position stress testing and weakness detection.", "capabilities": ["risk_review", "opposing_arguments", "strategy"]},
    {"id": "privilege_sentinel", "name": "Privilege Sentinel", "description": "Privilege, waiver, confidentiality, and disclosure risk warnings.", "capabilities": ["privilege", "confidentiality", "disclosure_risk"]},
    {"id": "client_intake", "name": "Client Intake Assistant", "description": "Structured intake questions and missing-fact collection.", "capabilities": ["intake", "facts", "client_questions"]},
    {"id": "enforcement_assistant", "name": "Enforcement Assistant", "description": "Post-resolution compliance, enforcement package, and retention workflow support.", "capabilities": ["enforcement", "compliance", "post_resolution"]},
]

MODES = [
    {"id": "fast", "label": "Fast", "description": "Short answers and quick triage.", "temperature": 0.2, "max_context_messages": 8},
    {"id": "balanced", "label": "Balanced", "description": "Default balanced depth and speed.", "temperature": 0.3, "max_context_messages": 16},
    {"id": "deep", "label": "Deep Analysis", "description": "Longer, structured analysis with more issue spotting.", "temperature": 0.1, "max_context_messages": 32},
    {"id": "creative", "label": "Creative Drafting", "description": "More drafting alternatives while preserving legal safety gates.", "temperature": 0.6, "max_context_messages": 20},
    {"id": "private_local", "label": "Private Local", "description": "Local/private provider preference; external providers disabled unless configured.", "temperature": 0.1, "max_context_messages": 12},
]

CHAT_TYPES = [
    {"id": "general", "label": "General", "requires_matter": False, "description": "No automatic confidential matter access."},
    {"id": "matter", "label": "Matter", "requires_matter": True, "description": "Scoped to an authorized matter."},
    {"id": "research", "label": "Research", "requires_matter": False, "description": "Legal research and authority workflow."},
    {"id": "drafting", "label": "Drafting", "requires_matter": False, "description": "Supervised drafting, rewriting, and editing."},
    {"id": "agent", "label": "Agent Task", "requires_matter": False, "description": "Plan-first multi-step work; execution requires approval."},
]

TOOLS = [
    {"id": "citation_verifier", "label": "Citation Verifier", "enabled": True, "risk": "medium"},
    {"id": "deadline_service", "label": "Deadline Service", "enabled": True, "risk": "high"},
    {"id": "evidence_linker", "label": "Evidence Linker", "enabled": True, "risk": "medium"},
    {"id": "privilege_guard", "label": "Privilege Guard", "enabled": True, "risk": "high"},
    {"id": "agent_planner", "label": "Agent Planner", "enabled": True, "risk": "high"},
]


def _ensure() -> None:
    init_db()
    with get_connection() as conn:
        for stmt in compat_schema_ddl(wrap_timestamp_defaults(_CHAT_DDL)):
            conn.execute(stmt)


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:14]}"


def _assert_matter(user: UserInfo, matter_id: Optional[str]) -> None:
    if not matter_id:
        return
    if not get_identity_service().can_access_matter(user, matter_id):
        raise AuthError("Matter access denied for this conversation")


@dataclass
class AssistantReply:
    content: str
    citations: list[dict[str, Any]] = field(default_factory=list)
    actions: list[dict[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    work_panel: Optional[dict[str, Any]] = None
    tool_activity: list[str] = field(default_factory=list)
    provider: str = "safe_local"
    model: str = "safe-orchestrator"
    usage: dict[str, int] = field(default_factory=dict)
    controls: dict[str, Any] = field(default_factory=dict)

    def to_meta(self) -> dict[str, Any]:
        return {
            "citations": self.citations,
            "actions": self.actions,
            "warnings": self.warnings,
            "work_panel": self.work_panel,
            "tool_activity": self.tool_activity,
            "provider": self.provider,
            "model": self.model,
            "usage": self.usage,
            "controls": self.controls,
        }


class ConversationService:
    def list_specialists(self) -> list[dict[str, str]]:
        return list(SPECIALISTS)

    def list_modes(self) -> list[dict[str, Any]]:
        return list(MODES)

    def list_chat_types(self) -> list[dict[str, Any]]:
        return list(CHAT_TYPES)

    def list_tools(self) -> list[dict[str, Any]]:
        return list(TOOLS)

    def list_model_providers(self) -> list[dict[str, Any]]:
        return get_model_provider_registry().list_providers()

    def capabilities(self) -> dict[str, Any]:
        return {
            "product": "BC Legal AI Conversational Platform",
            "court_ready_default": False,
            "legal_advice": False,
            "supports_streaming": True,
            "supports_matter_scoping": True,
            "supports_agent_plans": True,
            "supports_settings": True,
            "specialists": self.list_specialists(),
            "modes": self.list_modes(),
            "chat_types": self.list_chat_types(),
            "tools": self.list_tools(),
            "model_providers": self.list_model_providers(),
            "default_model_provider": get_model_provider_registry().default_provider_id(),
            "safety_gates": [
                "matter_authorization",
                "ethical_wall_deny_first",
                "citation_fail_closed",
                "deadline_human_confirmation_required",
                "privilege_warning",
                "no_autonomous_filing_or_service",
            ],
        }

    def create(
        self,
        *,
        user: UserInfo,
        title: str = "New chat",
        chat_type: str = "general",
        matter_id: Optional[str] = None,
        model_mode: str = "balanced",
        specialist: str = "bc_legal_associate",
    ) -> dict[str, Any]:
        _ensure()
        if chat_type == "matter" and not matter_id:
            raise ValueError("matter_id required for matter chat")
        if chat_type == "general" and matter_id:
            # General chat must not auto-bind confidential matter
            matter_id = None
        _assert_matter(user, matter_id)
        cid = _id("chat")
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO conversations
                (conversation_id, org_id, user_id, title, chat_type, matter_id, model_mode, specialist)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cid,
                    user.org_id,
                    user.user_id,
                    title[:200],
                    chat_type,
                    matter_id,
                    model_mode,
                    specialist,
                ),
            )
        return self.get(user, cid)

    def list_for_user(self, user: UserInfo) -> list[dict[str, Any]]:
        _ensure()
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT conversation_id, title, chat_type, matter_id, model_mode, specialist, updated_at
                FROM conversations
                WHERE user_id = ? AND org_id = ? AND archived = 0
                ORDER BY updated_at DESC
                LIMIT 100
                """,
                (user.user_id, user.org_id),
            ).fetchall()
        return [dict(r) for r in rows]

    def get(self, user: UserInfo, conversation_id: str) -> dict[str, Any]:
        _ensure()
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM conversations WHERE conversation_id = ? AND user_id = ?",
                (conversation_id, user.user_id),
            ).fetchone()
        if not row:
            raise AuthError("Conversation not found")
        return dict(row)

    def list_messages(self, user: UserInfo, conversation_id: str) -> list[dict[str, Any]]:
        self.get(user, conversation_id)
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT message_id, role, content, meta_json, created_at
                FROM chat_messages WHERE conversation_id = ?
                ORDER BY created_at ASC
                """,
                (conversation_id,),
            ).fetchall()
        out = []
        for r in rows:
            meta = json.loads(r["meta_json"] or "{}")
            out.append(
                {
                    "message_id": r["message_id"],
                    "role": r["role"],
                    "content": r["content"],
                    "meta": meta,
                    "created_at": r["created_at"],
                }
            )
        return out

    def _save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        meta: Optional[dict[str, Any]] = None,
    ) -> str:
        mid = _id("msg")
        now = now_iso()
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO chat_messages (message_id, conversation_id, role, content, meta_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (mid, conversation_id, role, content, json.dumps(meta or {})),
            )
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?",
                (now, conversation_id),
            )
        return mid

    def send(
        self,
        *,
        user: UserInfo,
        conversation_id: str,
        content: str,
        attachments: Optional[list[dict[str, Any]]] = None,
        provider: str = "",
        model: str = "",
        tools: Optional[list[str]] = None,
        response_format: str = "message",
        temperature: Optional[float] = None,
    ) -> dict[str, Any]:
        conv = self.get(user, conversation_id)
        _assert_matter(user, conv.get("matter_id"))
        text = (content or "").strip()
        if not text and not attachments:
            raise ValueError("Empty message")
        user_meta = {"attachments": attachments or []}
        user_msg_id = self._save_message(conversation_id, "user", text or "[attachment]", user_meta)
        reply = self._orchestrate(user, conv, text)
        asst_id = self._save_message(
            conversation_id, "assistant", reply.content, reply.to_meta()
        )
        # Auto-title first user message
        if conv.get("title") in ("New chat", "New Chat", ""):
            title = (text[:60] + "…") if len(text) > 60 else (text or "Chat")
            with get_connection() as conn:
                conn.execute(
                    "UPDATE conversations SET title = ? WHERE conversation_id = ?",
                    (title, conversation_id),
                )
        return {
            "user_message_id": user_msg_id,
            "assistant_message_id": asst_id,
            "assistant": {
                "role": "assistant",
                "content": reply.content,
                "meta": reply.to_meta(),
            },
        }

    def stream_tokens(
        self, user: UserInfo, conversation_id: str, content: str
    ) -> Iterator[str]:
        """Yield assistant text chunks then final JSON envelope (for SSE)."""
        result = self.send(user=user, conversation_id=conversation_id, content=content)
        text = result["assistant"]["content"]
        # chunk for streaming UX
        step = max(12, len(text) // 20)
        for i in range(0, len(text), step):
            yield text[i : i + step]
        yield "\n\n__META__" + json.dumps(result["assistant"]["meta"])

    def _orchestrate(
        self, user: UserInfo, conv: dict[str, Any], text: str
    ) -> AssistantReply:
        low = text.lower()
        warnings = [
            "Not legal advice. Human supervision required for any filing, service, or advice.",
        ]
        tools: list[str] = []
        citations: list[dict[str, Any]] = []
        actions: list[dict[str, str]] = [
            {"id": "verify_authorities", "label": "Verify Authorities"},
            {"id": "view_evidence", "label": "View Evidence"},
        ]
        work_panel: Optional[dict[str, Any]] = {"view": "sources", "title": "Sources"}

        # Matter isolation reminder
        if conv.get("chat_type") == "general":
            warnings.append("General Chat does not automatically access confidential matters.")
        elif conv.get("matter_id"):
            tools.append(f"Matter scope: {conv['matter_id']}")

        # Citation / s.56 safety
        if "s.56" in low or "s 56" in low or "section 56" in low:
            tools.append("citation_verifier")
            v = verify_citation(text, matter_id=conv.get("matter_id") or "", expected_topic="retaliatory_eviction")
            citations.append(v)
            if v["status"] == "REJECTED":
                warnings.append(
                    "Citation check REJECTED for incorrect RTA s.56 retaliation mapping. "
                    "Confirm section heading on BC Laws."
                )

        # Agent-style multi-step
        if any(k in low for k in ("book of authorities", "build the complete", "agent", "plan:")):
            tools.append("agent_planner")
            plan = [
                "Extract every authority from the draft",
                "Verify citation and existence",
                "Confirm treatment and binding weight",
                "Retrieve official or authorized copy",
                "Identify missing authorities",
                "Build the index",
                "Assemble bookmarked PDF",
                "Submit for human approval",
            ]
            body = (
                "**PLAN** (Agent Task Chat — scaffold)\n\n"
                + "\n".join(f"{i}. {p}" for i, p in enumerate(plan, 1))
                + "\n\nNo step will file, serve, or disclose without authorization."
            )
            actions = [
                {"id": "approve_plan", "label": "Approve Plan"},
                {"id": "edit_plan", "label": "Edit Plan"},
                {"id": "cancel_plan", "label": "Cancel"},
            ]
            work_panel = {"view": "agent", "title": "Agent Activity", "plan": plan}
            return AssistantReply(
                content=body,
                actions=actions,
                warnings=warnings,
                work_panel=work_panel,
                tool_activity=tools,
                citations=citations,
            )

        # JR / RTB analysis style
        if any(k in low for k in ("judicial review", "rtb decision", "grounds", "petition", "form 66")):
            tools.extend(["legal_analysis", "evidence_linker"])
            body = (
                "I can help structure a **supervised** judicial-review analysis "
                "(scaffold — not a filing).\n\n"
                "**Potential structure**\n"
                "1. Orders sought (Form 66)\n"
                "2. Procedural fairness grounds (record-linked)\n"
                "3. Patent unreasonableness / standard of review (confirm current law)\n"
                "4. Evidence gaps requiring human confirmation\n"
                "5. Authorities — verify on BC Laws / CanLII before reliance\n\n"
                "Flag anything not source-linked. I will not mark output court-ready "
                "until evidence, citation, privilege, and lawyer approval complete."
            )
            actions = [
                {"id": "open_analysis", "label": "Open Analysis"},
                {"id": "view_evidence", "label": "View Evidence"},
                {"id": "verify_authorities", "label": "Verify Authorities"},
                {"id": "draft_petition", "label": "Draft Petition"},
            ]
            work_panel = {
                "view": "legal_issues",
                "title": "Legal Issues",
                "issues": [
                    {"label": "Procedural fairness", "strength": "review_required"},
                    {"label": "Patent unreasonableness", "strength": "review_required"},
                    {"label": "Additional evidence", "strength": "gap"},
                ],
            }
            return AssistantReply(
                content=body,
                actions=actions,
                warnings=warnings,
                work_panel=work_panel,
                tool_activity=tools,
                citations=citations,
            )

        # Deadline questions — deterministic service only
        if any(k in low for k in ("deadline", "limitation", "60 day", "sixty day", "when is")):
            tools.append("deadline_service")
            warnings.append(
                "Deadline engine returns provisional states only. "
                "Only HUMAN_CONFIRMED dates may be treated as definitive."
            )
            body = (
                "For limitation and filing windows I use the **deterministic deadline service**, "
                "not free-form model guessing.\n\n"
                "Provide: forum, document type, service method, start date, and whether "
                "finality is known. I will return a state such as CALCULATED or "
                "HUMAN_REVIEW_REQUIRED — never a silent final client deadline."
            )
            actions = [
                {"id": "deadline_review", "label": "Deadline Review"},
                {"id": "require_lawyer", "label": "Require Lawyer Review"},
            ]
            work_panel = {"view": "deadlines", "title": "Deadline Review"}
            return AssistantReply(
                content=body,
                actions=actions,
                warnings=warnings,
                work_panel=work_panel,
                tool_activity=tools,
            )

        # Default conversational support
        tools.append("general_support")
        specialist = next(
            (s["name"] for s in SPECIALISTS if s["id"] == conv.get("specialist")),
            "BC Legal Associate",
        )
        body = (
            f"**{specialist}** (mode: {conv.get('model_mode', 'balanced')})\n\n"
            "I'm the conversational legal workspace scaffold. I can help organize "
            "research questions, structure JR/RTB analysis, flag citation risks, "
            "and prepare supervised drafts.\n\n"
            f"You said:\n> {text[:800]}\n\n"
            "Tell me the **matter**, **forum**, and whether you want research, "
            "evidence review, drafting, or an agent plan. "
            "I will not invent statute text — use BC Laws for official wording."
        )
        if re.search(r"\b(file|serve|settle|waive)\b", low):
            warnings.append(
                "I cannot autonomously file, serve, settle, or waive rights. "
                "Human authorization required."
            )
        return AssistantReply(
            content=body,
            actions=actions,
            warnings=warnings,
            work_panel=work_panel,
            tool_activity=tools,
            citations=citations,
        )


_svc: Optional[ConversationService] = None


def get_conversation_service() -> ConversationService:
    global _svc
    _ensure()
    if _svc is None:
        _svc = ConversationService()
    return _svc
