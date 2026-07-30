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
from backend.skills_runtime import (
    build_skill_context_block,
    catalog_summary,
    resolve_skills,
)

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
    {"id": "jr_counsel", "name": "Judicial Review Counsel", "description": "RTB/tribunal JR: ATA s.58 patent unreasonableness, Form 66, s.57 clock, stays, record review.", "capabilities": ["judicial_review", "ata_s58", "form_66", "drafting", "record_review"]},
    {"id": "statutory_interpreter", "name": "Statutory Interpreter", "description": "Text, context, scheme, purpose, consequences, and Vavilov statutory constraints.", "capabilities": ["statutory_interpretation", "scheme_analysis", "purpose_analysis"]},
    {"id": "legal_terminology", "name": "Legal Terminology Translator", "description": "Terminology cleanup, plain-language conversion, and doctrine distinction policing.", "capabilities": ["terminology", "plain_language", "draft_cleanup"]},
    {"id": "evidence_analyst", "name": "Evidence Analyst", "description": "Evidence matrix, gaps, chronology, propositions, and source-linking.", "capabilities": ["evidence", "chronology", "gap_analysis"]},
    {"id": "citation_clerk", "name": "Citation Clerk", "description": "Fail-closed citation triage and authority verification workflow.", "capabilities": ["citations", "authority_check", "court_ready_gate"]},
    {"id": "procedural_clerk", "name": "Procedural Clerk", "description": "Procedure checklists, filing steps, service, and forum-sensitive tasks.", "capabilities": ["procedure", "service", "forms"]},
    {"id": "deadline_clerk", "name": "Deadline Clerk", "description": "Provisional deadline collection and human-confirmation workflow.", "capabilities": ["deadlines", "jr_clock", "limitation_triage"]},
    {"id": "affidavit_drafter", "name": "Affidavit Drafter", "description": "Fact/evidence-separated affidavit outline support.", "capabilities": ["affidavits", "evidence", "drafting"]},
    {"id": "boa_builder", "name": "Book of Authorities Builder", "description": "Authority extraction, verification plan, and BOA assembly workflow.", "capabilities": ["authorities", "boa", "pinpoints"]},
    {"id": "cross_exam_planner", "name": "Cross-Examination Planner", "description": "Issue-driven cross-examination topics and impeachment planning.", "capabilities": ["cross_examination", "witnesses", "impeachment"]},
    {"id": "hearing_prep", "name": "Tribunal Hearing Prep", "description": "Record dissection, legal test, binders, outlines, witness coaching, Q&A simulation for RTB/BCHRT/JR.", "capabilities": ["hearing_prep", "record_review", "witnesses", "binders", "submissions"]},
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
    {"id": "summarize", "label": "Summarize", "enabled": True, "risk": "low"},
    {"id": "email_draft", "label": "Email Draft", "enabled": True, "risk": "low"},
    {"id": "creative", "label": "Creative Writing", "enabled": True, "risk": "low"},
    {"id": "research_plan", "label": "Research Plan", "enabled": True, "risk": "medium"},
    {"id": "web_research", "label": "Web Research (allowlisted)", "enabled": True, "risk": "medium"},
    {"id": "code_assistant", "label": "Code Assistant", "enabled": True, "risk": "low"},
    {"id": "arena", "label": "Arena AI", "enabled": True, "risk": "medium"},
    {"id": "openclaw", "label": "OpenClaw Agent", "enabled": True, "risk": "high"},
    {"id": "kimi", "label": "Kimi (Moonshot)", "enabled": True, "risk": "medium"},
    {"id": "hearing_prep", "label": "Tribunal Hearing Prep", "enabled": True, "risk": "medium"},
    {"id": "ollama", "label": "Ollama Local Models", "enabled": True, "risk": "low"},
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

    def list_skills_catalog(self) -> dict[str, Any]:
        return catalog_summary()

    def capabilities(self) -> dict[str, Any]:
        skills = catalog_summary()
        return {
            "product": "BC Legal AI Conversational Platform",
            "court_ready_default": False,
            "legal_advice": False,
            "supports_streaming": True,
            "supports_multi_turn_memory": True,
            "supports_matter_scoping": True,
            "supports_agent_plans": True,
            "supports_settings": True,
            "supports_skill_loading": True,
            "supports_ollama": True,
            "supports_arena": True,
            "supports_productivity_tools": True,
            "supports_code_assistant": True,
            "supports_web_research": True,
            "enterprise_ai_suite": True,
            "skills_loaded_count": skills.get("count", 0),
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
                "skill_pack_grounding",
                "design_locks_enforced",
            ],
            "design_locks": skills.get("locked_guards", []),
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
        client_content: str = "",
    ) -> dict[str, Any]:
        from backend.platform.ai_safety import assess_user_input, enforce_output_safety

        conv = self.get(user, conversation_id)
        _assert_matter(user, conv.get("matter_id"))
        text = (content or "").strip()
        if not text and not attachments:
            raise ValueError("Empty message")
        gate = assess_user_input(text)
        if not gate.allowed:
            user_msg_id = self._save_message(
                conversation_id, "user", text or "[attachment]", {"attachments": attachments or []}
            )
            asst_id = self._save_message(
                conversation_id,
                "assistant",
                gate.rewritten_content,
                {
                    "warnings": gate.reasons,
                    "controls": {"court_ready": False, "blocked": True},
                    "provider": "safety_gate",
                    "model": "policy",
                },
            )
            return {
                "user_message_id": user_msg_id,
                "assistant_message_id": asst_id,
                "assistant": {
                    "role": "assistant",
                    "content": gate.rewritten_content,
                    "meta": {"warnings": gate.reasons, "controls": {"blocked": True}},
                },
            }
        user_meta = {
            "attachments": attachments or [],
            "provider_request": provider or "",
            "model_request": model or "",
        }
        from backend.platform import org_admin
        from backend.platform.model_providers import get_model_provider_registry

        pid = provider or get_model_provider_registry().default_provider_id()
        if (conv.get("model_mode") or "") == "private_local" and not provider:
            pid = "ollama"
        qcheck = org_admin.check_quota(user, provider=pid)
        if not qcheck.get("allowed"):
            raise ValueError(qcheck.get("reason") or "AI quota denied")

        user_msg_id = self._save_message(conversation_id, "user", text or "[attachment]", user_meta)
        # Multi-turn memory: prior messages (excluding the one just saved is ok — include all)
        history = self.list_messages(user, conversation_id)

        # Browser Puter / Kimi path: UI already called puter.ai.chat(); we persist + safety-gate only.
        client_text = (client_content or "").strip()
        if client_text and pid in ("puter", "kimi"):
            mode = conv.get("model_mode") or "balanced"
            safe = enforce_output_safety(client_text, mode=mode)
            body = safe.rewritten_content or client_text
            client_model = model or (
                "moonshotai/kimi-k2.5" if pid == "kimi" else "gpt-5-nano"
            )
            warn = (
                "Kimi / Moonshot (browser · user-pays via Puter). "
                "Not legal advice. Outputs are never court-ready without human review."
                if pid == "kimi"
                else (
                    "Puter AI (browser · user-pays · https://developer.puter.com/ai/). "
                    "Not legal advice. Outputs are never court-ready without human review."
                )
            )
            reply = AssistantReply(
                content=body,
                warnings=[warn],
                provider=pid,
                model=client_model,
                usage={
                    "input_tokens": max(20, len(text) // 4),
                    "output_tokens": max(20, len(body) // 4),
                },
                controls={
                    "court_ready": False,
                    "legal_advice": False,
                    "client_side": True,
                    "user_pays": True,
                    "provider": pid,
                    "model": client_model,
                    "kimi": pid == "kimi",
                    "safety_tags": safe.tags,
                },
            )
        else:
            reply = self._orchestrate(
                user,
                conv,
                text,
                history=history,
                provider=provider,
                model=model,
                temperature=temperature,
            )
        # Telemetry (estimate tokens from usage or content length)
        in_t = int((reply.usage or {}).get("prompt_eval_count") or (reply.usage or {}).get("input_tokens") or max(20, len(text) // 4))
        out_t = int((reply.usage or {}).get("eval_count") or (reply.usage or {}).get("output_tokens") or max(20, len(reply.content) // 4))
        try:
            org_admin.record_usage(
                user,
                provider=reply.provider or pid,
                model=reply.model or model or "",
                feature="chat",
                input_tokens=in_t,
                output_tokens=out_t,
            )
        except Exception:
            pass
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
        self,
        user: UserInfo,
        conv: dict[str, Any],
        text: str,
        *,
        history: Optional[list[dict[str, Any]]] = None,
        provider: str = "",
        model: str = "",
        temperature: Optional[float] = None,
    ) -> AssistantReply:
        from backend.platform.ai_safety import enforce_output_safety, reasoning_scaffold
        from backend.platform.code_assistant import complete_code, debug_code, document_code
        from backend.platform.productivity_tools import (
            creative_writing,
            draft_email,
            research_plan,
            summarize_text,
        )

        low = text.lower()
        warnings = [
            "Not legal advice. Human supervision required for any filing, service, or advice.",
            "WORKING DRAFT — human verification required before filing.",
        ]
        tools: list[str] = []
        citations: list[dict[str, Any]] = []
        actions: list[dict[str, str]] = [
            {"id": "verify_authorities", "label": "Verify Authorities"},
            {"id": "view_evidence", "label": "View Evidence"},
        ]
        work_panel: Optional[dict[str, Any]] = {"view": "sources", "title": "Sources"}
        controls: dict[str, Any] = {"court_ready": False, "legal_advice": False}
        history = history or []

        # Load in-repo skills for this specialist + message
        specialist_id = conv.get("specialist") or "bc_legal_associate"
        active_skills = resolve_skills(specialist=specialist_id, message=text, limit=4)
        skill_names = [s.name for s in active_skills]
        if skill_names:
            tools.append("skills:" + ",".join(skill_names))
        skill_block = build_skill_context_block(active_skills, per_skill_chars=1600)
        controls["skills_loaded"] = skill_names

        # Matter isolation reminder
        if conv.get("chat_type") == "general":
            warnings.append("General Chat does not automatically access confidential matters.")
        elif conv.get("matter_id"):
            tools.append(f"Matter scope: {conv['matter_id']}")

        # Deterministic JR clock when issuance-like cues present
        jr_clock_block = ""
        if any(k in low for k in ("jr clock", "60 day", "sixty day", "limitation", "s.57", "issuance")):
            tools.append("deadline_service")
            iss = None
            m_date = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
            if m_date:
                iss = m_date.group(1)
            try:
                from services.deadlines.jr_clock import JrClockRequest, calculate_jr_clock

                clock = calculate_jr_clock(
                    JrClockRequest(
                        matter_id=str(conv.get("matter_id") or "CHAT"),
                        issuance_date=iss,
                        finality_known="finality unknown" not in low and "not final" not in low,
                        enabling_act_known="enabling" not in low or "ata" in low or "s.57" in low,
                        extension_sought="extension" in low or "s.57(2)" in low,
                        human_confirmed=False,
                    )
                )
                jr_clock_block = (
                    "\n\n### JR clock (deterministic — not filing advice)\n"
                    f"- Mode: `{clock.clock_mode.value}`\n"
                    f"- Primary deadline: {clock.primary_deadline or 'n/a'}\n"
                    f"- HITL required: {clock.hitl_required}\n"
                    f"- Display: {clock.client_display}\n"
                )
                if clock.alternatives:
                    lines = []
                    for a in clock.alternatives:
                        if isinstance(a, dict):
                            label = a.get("label") or a.get("mode") or "alternative"
                            deadline = a.get("deadline")
                            note = a.get("note")
                            bit = f"{label}"
                            if deadline:
                                bit += f" → {deadline}"
                            if note:
                                bit += f" ({note})"
                            lines.append(f"  - {bit}")
                        else:
                            lines.append(f"  - {a}")
                    jr_clock_block += "- Alternatives:\n" + "\n".join(lines)
                warnings.append(
                    "Only HUMAN_CONFIRMED limitation dates may be treated as definitive."
                )
            except Exception as exc:  # pragma: no cover - defensive
                warnings.append(f"JR clock module unavailable: {exc}")

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

        def _pack(body: str, **kwargs: Any) -> AssistantReply:
            """Attach skills footer/disclaimer uniformly."""
            skills_note = ""
            if skill_names:
                skills_note = (
                    "\n\n---\n"
                    f"**Skills loaded:** {', '.join(f'`{n}`' for n in skill_names)}\n"
                    "Apply category labels. Forms: petition **Form 66** (not 67); "
                    "interlocutory ≈ **Form 32**/**33**; affidavit **Form 109**. "
                    "Statute text: BC Laws only. Not legal advice."
                )
            content = body + jr_clock_block + skills_note
            # Keep a compact skill digest in controls for UI/debug (not full body)
            controls["skill_excerpt_chars"] = len(skill_block)
            return AssistantReply(
                content=content,
                citations=kwargs.get("citations", citations),
                actions=kwargs.get("actions", actions),
                warnings=kwargs.get("warnings", warnings),
                work_panel=kwargs.get("work_panel", work_panel),
                tool_activity=kwargs.get("tool_activity", tools),
                controls=controls,
            )

        # --- Productivity suite (Monica-style) ---
        if low.startswith("/summarize") or low.startswith("summarize:"):
            tools.append("summarize")
            payload = text.split(":", 1)[-1] if ":" in text else text.replace("/summarize", "", 1)
            # Use prior user message body if short command
            if len(payload.strip()) < 20 and len(history) >= 2:
                payload = history[-2].get("content") or payload
            res = summarize_text(payload.strip())
            return _pack(res.content, work_panel={"view": "productivity", "title": "Summary", "tool": "summarize"})

        if low.startswith("/email") or "draft an email" in low or "draft email" in low:
            tools.append("email_draft")
            res = draft_email(purpose=text, audience="counsel", points=[])
            return _pack(res.content, work_panel={"view": "productivity", "title": "Email draft", "tool": "email"})

        if low.startswith("/creative") or low.startswith("write a story"):
            tools.append("creative")
            res = creative_writing(text)
            return _pack(res.content, work_panel={"view": "productivity", "title": "Creative", "tool": "creative"})

        if low.startswith("/research") or low.startswith("research plan"):
            tools.append("research_plan")
            res = research_plan(text)
            return _pack(res.content, work_panel={"view": "research", "title": "Research plan", "tool": "research"})

        # --- Copilot-style code ---
        if low.startswith("/code") or low.startswith("/debug") or low.startswith("/document-code"):
            tools.append("code_assistant")
            if low.startswith("/debug"):
                res = debug_code(text, error="")
            elif low.startswith("/document-code"):
                res = document_code(text)
            else:
                res = complete_code(text)
            return _pack(res.content, work_panel={"view": "code", "title": "Code assist", "tool": res.mode})

        # --- OpenClaw agent harness ---
        if low.startswith("/claw") or low.startswith("/openclaw") or low.startswith("openclaw:"):
            tools.append("openclaw")
            from backend.platform import openclaw as claw

            goal = text
            for prefix in ("/openclaw", "/claw", "openclaw:"):
                if low.startswith(prefix.lower()) or text.lower().startswith(prefix):
                    goal = text[len(prefix) :].lstrip(" :")
                    break
            if len(goal.strip()) < 3:
                goal = text
            run = claw.run_agent(user, goal.strip(), auto_approve=False, execute=True)
            return AssistantReply(
                content=run.get("summary") or "OpenClaw run complete.",
                warnings=warnings + list(run.get("warnings") or []),
                work_panel={
                    "view": "openclaw",
                    "title": "OpenClaw agent",
                    "run_id": run.get("run_id"),
                    "status": run.get("status"),
                    "plan": run.get("plan"),
                    "steps": run.get("steps"),
                },
                tool_activity=tools + ["openclaw"],
                provider="openclaw",
                model="legal-harness",
                controls={
                    **controls,
                    "openclaw": True,
                    "court_ready": False,
                    "run_id": run.get("run_id"),
                },
            )

        # --- Tribunal hearing prep workflow ---
        if (
            low.startswith("/hearing")
            or low.startswith("/hearing-prep")
            or low.startswith("hearing prep")
            or "dissect the decision" in low
            or "tabbed binder" in low
        ):
            tools.append("hearing_prep")
            skills = resolve_skills(specialist="hearing_prep", message=text, limit=4)
            skill_names = [s.name for s in skills]
            skill_block = build_skill_context_block(skills, per_skill_chars=1200)
            body = (
                "# Tribunal / JR hearing preparation (structured)\n\n"
                "**Not legal advice.** Human counsel owns strategy and any filing.\n\n"
                "## A — Dissect the record and the law\n"
                "1. **Read the whole record** — decision, transcripts/notes, exhibits filed below.\n"
                "2. Log **factual errors** (finding vs evidence) and **procedural unfairness**.\n"
                "3. State the **legal test / standard of review** for this forum "
                "(e.g. patent unreasonableness / fairness-correctness for RTB JR — verify ATA).\n"
                "4. Map **governing legislation** via BC Laws only; plan authorities on CanLII.\n\n"
                "## B — Organize materials\n"
                "1. Build a **tabbed binder index** (physical or PDF bookmarks).\n"
                "2. Draft **opening**, **core facts** (pinned), **concise submissions**.\n\n"
                "## C — Witnesses and arguments\n"
                "1. Coach witnesses: answer only the question; don’t guess; personal knowledge.\n"
                "2. **Simulate hard Q&A** (tribunal + cross).\n"
                "3. Day-of checklist: tabs open, quiet connection, accommodations.\n\n"
                f"**Your request:** {text[:2000]}\n\n"
                "### Next structured outputs you can request\n"
                "- `RECORD_MAP` · `BINDER_INDEX` · `OPENING` · `SUBMISSIONS` · `QA_SIM`\n"
                "- Or run OpenClaw: `/claw hearing prep binder and witness Q&A for this RTB JR`\n"
                "- Specialist: select **Tribunal Hearing Prep** in the UI\n\n"
                f"{skill_block[:2500]}\n\n"
                "Templates: `skills/tribunal-hearing-prep/templates/` "
                "(binder-index, hearing-outline, witness-qa-sim).\n\n"
                "If you name the tribunal (**RTB**, **BCHRT**, **JR**, other), steps will be tailored further."
            )
            return _pack(
                body,
                work_panel={
                    "view": "hearing_prep",
                    "title": "Tribunal hearing preparation",
                    "phases": ["dissect_record", "organize_binder", "witness_qa"],
                    "skills": skill_names,
                },
                tool_activity=tools + skill_names,
            )

        # --- Kimi routing hint (browser path uses provider=kimi + client_content) ---
        if low.startswith("/kimi"):
            tools.append("kimi")
            payload = text.split(":", 1)[-1].strip() if ":" in text else text.replace("/kimi", "", 1).strip()
            body = (
                "**Kimi (Moonshot)** is selected for deep / long-context work.\n\n"
                f"Prompt queued: {payload[:1500] or '(empty — type your question after /kimi)'}\n\n"
                "Switch provider to **Kimi** in the toolbar (or keep it selected) and send your "
                "full question. Browser path uses Puter model `moonshotai/kimi-k2.5` (user-pays). "
                "Optional server: `MOONSHOT_API_KEY` + `ALA_ALLOW_EXTERNAL_LLM=1`.\n\n"
                "Not legal advice. court_ready=false."
            )
            return _pack(
                body,
                work_panel={"view": "kimi", "title": "Kimi routing", "model": "moonshotai/kimi-k2.5"},
            )

        # Deep analysis mode → structured reasoning scaffold prefix
        deep_prefix = ""
        if conv.get("model_mode") == "deep" or "think step by step" in low:
            tools.append("extended_reasoning")
            deep_prefix = reasoning_scaffold(text) + "\n\n"

        # Agent-style multi-step
        if any(k in low for k in ("book of authorities", "build the complete", "agent", "plan:")):
            tools.append("agent_planner")
            plan = [
                "Extract every authority from the draft",
                "Verify citation and existence (CanLII / official) — no fabricated cites",
                "Confirm treatment and binding weight",
                "Retrieve official or authorized copy",
                "Identify missing authorities",
                "Build the index (court BOA discipline)",
                "Assemble bookmarked PDF on filing day",
                "Submit for human approval",
            ]
            body = (
                "**PLAN** (Agent Task Chat — scaffold)\n\n"
                + "\n".join(f"{i}. {p}" for i, p in enumerate(plan, 1))
                + "\n\nNo step will file, serve, or disclose without authorization."
            )
            if skill_block:
                body += "\n\n" + skill_block[:1200]
            return _pack(
                body,
                actions=[
                    {"id": "approve_plan", "label": "Approve Plan"},
                    {"id": "edit_plan", "label": "Edit Plan"},
                    {"id": "cancel_plan", "label": "Cancel"},
                ],
                work_panel={"view": "agent", "title": "Agent Activity", "plan": plan},
            )

        # JR / RTB analysis style
        if any(
            k in low
            for k in (
                "judicial review",
                "rtb decision",
                "grounds",
                "petition",
                "form 66",
                "form 67",
                "patent unreason",
                "procedural fairness",
            )
        ):
            tools.extend(["legal_analysis", "evidence_linker", "skill_pack"])
            body = (
                "I can help structure a **supervised** judicial-review analysis "
                "(WORKING DRAFT — not a filing).\n\n"
                "**Potential structure**\n"
                "1. Orders sought (**Form 66** petition — Form 67 is the *response*)\n"
                "2. Procedural fairness grounds (correctness; record-linked)\n"
                "3. **ATA s.58** patent unreasonableness for typical RTB fact/law "
                "(do not default-label as Vavilov reasonableness without checking ATA)\n"
                "4. JR clock — **60 days from issuance** of final decision when s.57 applies; "
                "alternatives if finality/date/Act uncertain\n"
                "5. Evidence gaps requiring human confirmation\n"
                "6. Authorities — verify on BC Laws / CanLII before reliance\n\n"
                "Label FACT / ALLEGATION / ARGUMENT / INFERENCE / ASSUMPTION.\n"
                "I will not mark output court-ready until evidence, citation, privilege, "
                "and human approval complete."
            )
            if skill_block:
                body += "\n\n" + skill_block[:2000]
            return _pack(
                body,
                actions=[
                    {"id": "open_analysis", "label": "Open Analysis"},
                    {"id": "view_evidence", "label": "View Evidence"},
                    {"id": "verify_authorities", "label": "Verify Authorities"},
                    {"id": "draft_petition", "label": "Draft Petition (Form 66)"},
                ],
                work_panel={
                    "view": "legal_issues",
                    "title": "Legal Issues",
                    "issues": [
                        {"label": "Procedural fairness (correctness)", "strength": "review_required"},
                        {"label": "Patent unreasonableness (ATA s.58)", "strength": "review_required"},
                        {"label": "JR clock / finality", "strength": "review_required"},
                        {"label": "Additional evidence", "strength": "gap"},
                    ],
                    "skills": skill_names,
                },
            )

        # Deadline questions — deterministic service only
        if any(k in low for k in ("deadline", "limitation", "60 day", "sixty day", "when is", "jr clock")):
            tools.append("deadline_service")
            warnings.append(
                "Deadline engine returns provisional states only. "
                "Only HUMAN_CONFIRMED dates may be treated as definitive."
            )
            body = (
                "For limitation and filing windows I use the **deterministic deadline / JR clock "
                "service**, not free-form model guessing.\n\n"
                "Provide: forum, document type, service method, **issuance date** (YYYY-MM-DD), "
                "whether finality is known, and whether ATA s.57 applies. "
                "I return modes such as STANDARD_60_FROM_ISSUANCE or FINALITY_UNCERTAIN — "
                "never a silent final client deadline.\n\n"
                "Petition form: **Form 66**. Stay / interlocutory: generally **Form 32**."
            )
            if skill_block:
                body += "\n\n" + skill_block[:1200]
            return _pack(
                body,
                actions=[
                    {"id": "deadline_review", "label": "Deadline Review"},
                    {"id": "require_lawyer", "label": "Require Lawyer Review"},
                ],
                work_panel={"view": "deadlines", "title": "Deadline Review", "skills": skill_names},
            )

        # Default: multi-turn provider completion (ChatGPT-style) + skill grounding
        tools.append("multi_turn_chat")
        specialist_name = next(
            (s["name"] for s in SPECIALISTS if s["id"] == specialist_id),
            "BC Legal Associate",
        )
        mode = conv.get("model_mode") or "balanced"
        mode_meta = next((m for m in MODES if m["id"] == mode), MODES[1])
        max_ctx = int(mode_meta.get("max_context_messages") or 16)
        temp = (
            float(temperature)
            if temperature is not None
            else float(mode_meta.get("temperature") or 0.3)
        )

        # Build chat history for provider (exclude trailing assistant if any)
        chat_msgs: list[dict[str, str]] = []
        for m in history[-max_ctx:]:
            role = m.get("role") or "user"
            if role not in ("user", "assistant", "system"):
                continue
            chat_msgs.append({"role": role, "content": str(m.get("content") or "")[:8000]})
        if not chat_msgs or chat_msgs[-1].get("role") != "user":
            chat_msgs.append({"role": "user", "content": text})

        system = (
            f"You are {specialist_name} in the BC Legal AI Associate supervised workspace. "
            "Be helpful, honest, and harmless. Never claim to be a lawyer or give legal advice. "
            "Never mark outputs court-ready. Prefer structured answers. "
            "For BC law, direct users to verify on BC Laws. "
            "Form 66 = petition; Form 67 = response. "
            f"Skills context:\n{skill_block[:3000]}"
        )
        reg = get_model_provider_registry()
        pid = provider or reg.default_provider_id()
        if mode == "private_local" and not provider:
            pid = "ollama"
        req = ChatModelRequest(
            messages=chat_msgs,
            system_prompt=system,
            model=model or "safe-orchestrator",
            mode=mode,
            temperature=temp,
            max_tokens=2048 if mode != "deep" else 4096,
            metadata={"specialist": specialist_id, "conversation_id": conv.get("conversation_id")},
        )
        resp = reg.complete(req, provider_id=pid)
        safe = enforce_output_safety(resp.content, mode=mode)
        body = deep_prefix + (safe.rewritten_content or resp.content)
        if skill_names and "skills loaded" not in body.lower():
            body += (
                "\n\n---\n"
                f"**Skills loaded:** {', '.join(f'`{n}`' for n in skill_names)}"
            )
        if re.search(r"\b(file|serve|settle|waive)\b", low):
            warnings.append(
                "I cannot autonomously file, serve, settle, or waive rights. "
                "Human authorization required."
            )
        controls["provider"] = resp.provider
        controls["model"] = resp.model
        controls["finish_reason"] = resp.finish_reason
        controls["safety_tags"] = safe.tags
        controls["multi_turn_messages"] = len(chat_msgs)
        return AssistantReply(
            content=body + jr_clock_block,
            citations=citations,
            actions=actions,
            warnings=warnings + [f"Provider: {resp.provider}/{resp.model}"],
            work_panel=work_panel,
            tool_activity=tools,
            provider=resp.provider,
            model=resp.model,
            usage=resp.usage or {},
            controls=controls,
        )


_svc: Optional[ConversationService] = None


def get_conversation_service() -> ConversationService:
    global _svc
    _ensure()
    if _svc is None:
        _svc = ConversationService()
    return _svc
