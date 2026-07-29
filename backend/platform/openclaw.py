"""OpenClaw-inspired agent harness for BC Legal AI Associate.

Inspired by OpenClaw (https://openclaw.ai/) — open-source personal agent
patterns: multi-step plans, tool plugins, session memory, heartbeats.

Legal adaptations (fail-closed):
  - No autonomous filing, service, settlement, or privilege waiver
  - High-risk tools require human approval
  - court_ready always false; not legal advice
  - Tools are in-process plugins (skills, research, deadlines, citations)
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from backend.db import get_connection, init_db
from backend.db.helpers import now_iso
from backend.identity import UserInfo
from backend.platform.ai_safety import assess_user_input, enforce_output_safety

_MEMORY_DDL = """
CREATE TABLE IF NOT EXISTS openclaw_memory (
  memory_id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  key TEXT NOT NULL,
  value TEXT NOT NULL DEFAULT '',
  tags_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL DEFAULT '',
  updated_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS openclaw_runs (
  run_id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  goal TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'completed',
  plan_json TEXT NOT NULL DEFAULT '[]',
  steps_json TEXT NOT NULL DEFAULT '[]',
  result_summary TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT ''
);
"""

# Hard-blocked action patterns (OpenClaw autonomy capped for legal safety)
_BLOCKED_ACTION_RE = re.compile(
    r"\b(file|serve|settlement|settle|waive privilege|send to court|e-file|efile)\b",
    re.I,
)


@dataclass
class ClawTool:
    id: str
    label: str
    description: str
    risk: str = "low"  # low | medium | high
    requires_approval: bool = False
    category: str = "general"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "description": self.description,
            "risk": self.risk,
            "requires_approval": self.requires_approval,
            "category": self.category,
        }


@dataclass
class ClawStep:
    tool_id: str
    title: str
    status: str  # planned | ran | skipped | blocked | needs_approval
    output: str = ""
    risk: str = "low"
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "title": self.title,
            "status": self.status,
            "output": self.output,
            "risk": self.risk,
            "meta": self.meta,
        }


def _ensure() -> None:
    init_db()
    with get_connection() as conn:
        for stmt in _MEMORY_DDL.split(";"):
            s = stmt.strip()
            if s:
                conn.execute(s)


def list_tools() -> list[dict[str, Any]]:
    """Plugin tool catalog (OpenClaw-style skills surface)."""
    tools = [
        ClawTool(
            "triage",
            "Matter Triage",
            "Classify forum, urgency, and next procedural questions.",
            risk="low",
            category="legal",
        ),
        ClawTool(
            "skill_pack",
            "Skill Pack Loader",
            "Load in-repo legal skill packs relevant to the goal.",
            risk="low",
            category="skills",
        ),
        ClawTool(
            "summarize",
            "Summarize",
            "Extractive summary of long text in the goal.",
            risk="low",
            category="productivity",
        ),
        ClawTool(
            "research_plan",
            "Research Plan",
            "Structured research plan for the legal issue.",
            risk="medium",
            category="research",
        ),
        ClawTool(
            "web_research",
            "Allowlisted Web Research",
            "Bounded public/official research (host allowlist).",
            risk="medium",
            category="research",
        ),
        ClawTool(
            "jr_clock",
            "JR Clock",
            "Deterministic ATA s.57 judicial review limitation clock.",
            risk="high",
            requires_approval=True,
            category="deadlines",
        ),
        ClawTool(
            "citation_check",
            "Citation Gate",
            "Fail-closed citation verification scaffold.",
            risk="medium",
            category="citations",
        ),
        ClawTool(
            "draft_outline",
            "Draft Outline",
            "Supervised outline for petition, affidavit, or letter.",
            risk="medium",
            category="drafting",
        ),
        ClawTool(
            "privilege_scan",
            "Privilege Sentinel",
            "Flag privilege / confidentiality risk language.",
            risk="high",
            requires_approval=True,
            category="privilege",
        ),
        ClawTool(
            "memory_write",
            "Session Memory",
            "Store a short key fact for this org user (synthetic-safe).",
            risk="low",
            category="memory",
        ),
        ClawTool(
            "memory_read",
            "Recall Memory",
            "Recall recent OpenClaw memory notes for this user.",
            risk="low",
            category="memory",
        ),
        ClawTool(
            "arena_hint",
            "Arena Hint",
            "Suggest multi-model Arena comparison for the goal.",
            risk="low",
            category="arena",
        ),
        ClawTool(
            "kimi_deep",
            "Kimi Deep Analysis",
            "Flag goal for long-context Kimi (Moonshot) analysis via Puter.",
            risk="medium",
            category="models",
        ),
    ]
    return [t.to_dict() for t in tools]


def _tool_map() -> dict[str, ClawTool]:
    return {t["id"]: ClawTool(**{k: t[k] for k in ("id", "label", "description", "risk", "requires_approval", "category")}) for t in list_tools()}


def plan_goal(goal: str) -> list[dict[str, str]]:
    """Heuristic multi-step plan (deterministic; model-optional)."""
    g = (goal or "").lower()
    steps: list[dict[str, str]] = [
        {"tool_id": "triage", "title": "Triage goal and constraints"},
        {"tool_id": "skill_pack", "title": "Load relevant skill packs"},
        {"tool_id": "memory_read", "title": "Recall prior session notes"},
    ]
    if len(goal) > 400 or "summar" in g:
        steps.append({"tool_id": "summarize", "title": "Summarize source material"})
    if any(k in g for k in ("research", "authority", "case law", "statute", "rta", "jr")):
        steps.append({"tool_id": "research_plan", "title": "Build research plan"})
        steps.append({"tool_id": "web_research", "title": "Allowlisted research"})
    if any(k in g for k in ("60 day", "jr clock", "limitation", "s.57", "deadline")):
        steps.append({"tool_id": "jr_clock", "title": "Compute JR clock (HITL)"})
    if any(k in g for k in ("cite", "citation", "authority", "scc", "bcca")):
        steps.append({"tool_id": "citation_check", "title": "Citation fail-closed check"})
    if any(k in g for k in ("draft", "petition", "affidavit", "form 66", "letter", "outline")):
        steps.append({"tool_id": "draft_outline", "title": "Supervised draft outline"})
    if any(k in g for k in ("privilege", "confidential", "solicitor", "without prejudice")):
        steps.append({"tool_id": "privilege_scan", "title": "Privilege risk scan"})
    if any(k in g for k in ("kimi", "long context", "deep analysis", "long document")):
        steps.append({"tool_id": "kimi_deep", "title": "Route to Kimi long-context"})
    if any(k in g for k in ("arena", "compare models", "which model")):
        steps.append({"tool_id": "arena_hint", "title": "Suggest Arena comparison"})
    steps.append({"tool_id": "memory_write", "title": "Persist goal snapshot to memory"})
    # de-dupe by tool_id preserve order
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for s in steps:
        if s["tool_id"] not in seen:
            seen.add(s["tool_id"])
            out.append(s)
    return out


def _run_tool(tool_id: str, goal: str, user: UserInfo, auto_approve: bool) -> ClawStep:
    tools = _tool_map()
    meta_tool = tools.get(tool_id)
    if not meta_tool:
        return ClawStep(tool_id, "Unknown tool", "skipped", f"Unknown tool `{tool_id}`")

    if meta_tool.requires_approval and not auto_approve:
        return ClawStep(
            tool_id,
            meta_tool.label,
            "needs_approval",
            f"**Human approval required** for high-risk tool `{tool_id}` "
            f"({meta_tool.description}). Re-run with `auto_approve=true` after review.",
            risk=meta_tool.risk,
            meta={"requires_approval": True},
        )

    if _BLOCKED_ACTION_RE.search(goal) and tool_id in ("draft_outline", "jr_clock"):
        # still allow planning/analysis but flag
        pass

    try:
        if tool_id == "triage":
            forums = []
            gl = goal.lower()
            if any(k in gl for k in ("rtb", "tenancy", "landlord", "tenant", "evict")):
                forums.append("RTB")
            if any(k in gl for k in ("jr", "judicial review", "petition", "form 66", "ata")):
                forums.append("BCSC JR")
            if any(k in gl for k in ("bchrt", "human rights", "discrimination")):
                forums.append("BCHRT")
            if not forums:
                forums.append("General / unclear — gather facts")
            out = (
                f"**Triage**\n- Possible forum(s): {', '.join(forums)}\n"
                "- Urgency: assess limitation / hearing dates with human confirmation\n"
                "- Next: missing facts, evidence list, desired remedy\n"
                "- **Not legal advice.** court_ready=false"
            )
            return ClawStep(tool_id, meta_tool.label, "ran", out, meta_tool.risk)

        if tool_id == "skill_pack":
            from backend.skills_runtime import build_skill_context_block, resolve_skills

            skills = resolve_skills(specialist="bc_legal_associate", message=goal, limit=4)
            names = [s.name for s in skills]
            block = build_skill_context_block(skills, per_skill_chars=900)
            out = f"**Skills loaded:** {', '.join(f'`{n}`' for n in names) or 'none'}\n\n{block[:2500]}"
            return ClawStep(tool_id, meta_tool.label, "ran", out, meta_tool.risk, {"skills": names})

        if tool_id == "summarize":
            from backend.platform.productivity_tools import summarize_text

            r = summarize_text(goal, max_bullets=6)
            return ClawStep(tool_id, meta_tool.label, "ran", r.content, meta_tool.risk)

        if tool_id == "research_plan":
            from backend.platform.productivity_tools import research_plan

            r = research_plan(goal)
            return ClawStep(tool_id, meta_tool.label, "ran", r.content, meta_tool.risk)

        if tool_id == "web_research":
            from backend.platform.web_research import research

            r = research(goal[:500], max_results=5)
            lines = [f"- [{x.get('title')}]({x.get('url')}) — {x.get('snippet', '')[:160]}" for x in (r.results or [])]
            out = f"**Allowlisted research** (live={r.live})\n" + "\n".join(lines[:8])
            out += "\n\ncourt_ready=false · verify on primary sources."
            return ClawStep(tool_id, meta_tool.label, "ran", out, meta_tool.risk, {"live": r.live})

        if tool_id == "jr_clock":
            iss = None
            m = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", goal)
            if m:
                iss = m.group(1)
            try:
                from services.deadlines.jr_clock import JrClockRequest, calculate_jr_clock

                clock = calculate_jr_clock(
                    JrClockRequest(
                        matter_id="OPENCLAW",
                        issuance_date=iss,
                        finality_known="final" in goal.lower() and "not final" not in goal.lower(),
                        enabling_act_known=True,
                        extension_sought="extension" in goal.lower(),
                        human_confirmed=auto_approve,
                    )
                )
                out = (
                    f"**JR clock (deterministic)**\n"
                    f"- Mode: `{clock.clock_mode.value}`\n"
                    f"- Primary: {clock.primary_deadline or 'n/a'}\n"
                    f"- HITL: {clock.hitl_required}\n"
                    f"- {clock.client_display}\n"
                    "- Not a filing deadline guarantee. Counsel confirmation required."
                )
                return ClawStep(tool_id, meta_tool.label, "ran", out, meta_tool.risk)
            except Exception as e:
                return ClawStep(tool_id, meta_tool.label, "ran", f"JR clock unavailable: {e}", meta_tool.risk)

        if tool_id == "citation_check":
            from backend.platform.citations import verify_citation

            cites = re.findall(
                r"\b(?:\d{4}\s+SCC\s+\d+|[A-Z][A-Za-z]+\s+v\.?\s+[A-Z][A-Za-z]+)\b",
                goal,
            )
            if not cites:
                out = (
                    "**Citation gate:** no clear citation patterns found. "
                    "Do not invent authorities. Prefer official reporters / CanLII after verification."
                )
            else:
                parts = []
                for c in cites[:5]:
                    v = verify_citation(c)
                    parts.append(f"- `{c}` → {v.get('status', 'unknown')} · {v.get('reasons', v)}")
                out = "**Citation gate (fail-closed)**\n" + "\n".join(parts)
            return ClawStep(tool_id, meta_tool.label, "ran", out, meta_tool.risk)

        if tool_id == "draft_outline":
            out = (
                "**Supervised draft outline** (not for filing)\n"
                "1. Parties & forum\n"
                "2. Decision under review / issues (FACT vs ALLEGATION vs ARGUMENT)\n"
                "3. Grounds (e.g. patent unreasonableness / fairness) with pinpoints TBD\n"
                "4. Relief sought\n"
                "5. Evidence list & record gaps\n"
                "6. Procedure checklist (service, timelines) — human ownership\n\n"
                "Form 66 = petition; Form 67 = response. court_ready=false."
            )
            return ClawStep(tool_id, meta_tool.label, "ran", out, meta_tool.risk)

        if tool_id == "privilege_scan":
            hits = []
            for pat, label in (
                (r"\bwithout prejudice\b", "without prejudice"),
                (r"\bsolicitor[- ]client\b", "solicitor-client"),
                (r"\bprivileged\b", "privileged"),
                (r"\bwaive\b", "waiver language"),
            ):
                if re.search(pat, goal, re.I):
                    hits.append(label)
            out = (
                f"**Privilege scan:** {', '.join(hits) if hits else 'no strong privilege cues in goal text'}.\n"
                "Do not disclose privileged content to third parties. "
                "No autonomous waiver. Human privilege review required."
            )
            return ClawStep(tool_id, meta_tool.label, "ran", out, meta_tool.risk, {"hits": hits})

        if tool_id == "memory_read":
            notes = list_memory(user, limit=5)
            if not notes:
                out = "No OpenClaw memory notes yet for this user."
            else:
                out = "**Recent memory**\n" + "\n".join(
                    f"- `{n['key']}`: {n['value'][:200]}" for n in notes
                )
            return ClawStep(tool_id, meta_tool.label, "ran", out, meta_tool.risk)

        if tool_id == "memory_write":
            key = f"goal_{now_iso()[:10]}"
            val = goal[:500]
            write_memory(user, key=key, value=val, tags=["goal", "openclaw"])
            return ClawStep(
                tool_id,
                meta_tool.label,
                "ran",
                f"Stored memory key `{key}` ({len(val)} chars).",
                meta_tool.risk,
            )

        if tool_id == "arena_hint":
            out = (
                "**Arena AI:** compare models on this goal via provider lineup "
                "`safe_local`, `kimi`, `puter` (and Ollama if local). "
                "Use the Arena panel or POST `/v1/platform/ai/arena` with preset `legal_core`."
            )
            return ClawStep(tool_id, meta_tool.label, "ran", out, meta_tool.risk)

        if tool_id == "kimi_deep":
            out = (
                "**Kimi (Moonshot):** recommended for long-context / deep analysis.\n"
                "- Provider: `kimi` · model: `moonshotai/kimi-k2.5` (via Puter user-pays)\n"
                "- Or set `MOONSHOT_API_KEY` + `ALA_ALLOW_EXTERNAL_LLM=1` for server path\n"
                "Switch the toolbar provider to **Kimi** for the next chat turn."
            )
            return ClawStep(tool_id, meta_tool.label, "ran", out, meta_tool.risk)

        return ClawStep(tool_id, meta_tool.label, "skipped", "No handler", meta_tool.risk)
    except Exception as e:
        return ClawStep(tool_id, meta_tool.label if meta_tool else tool_id, "blocked", f"Tool error: {e}", "high")


def run_agent(
    user: UserInfo,
    goal: str,
    *,
    auto_approve: bool = False,
    max_steps: int = 10,
    execute: bool = True,
) -> dict[str, Any]:
    """Plan and optionally execute an OpenClaw-style multi-tool run."""
    _ensure()
    goal = (goal or "").strip()
    if not goal:
        raise ValueError("goal required")

    gate = assess_user_input(goal)
    if not gate.allowed:
        return {
            "run_id": "",
            "ok": False,
            "status": "blocked",
            "goal": goal,
            "plan": [],
            "steps": [],
            "summary": gate.rewritten_content,
            "court_ready": False,
            "legal_advice": False,
            "openclaw": True,
            "warnings": gate.reasons,
        }

    if _BLOCKED_ACTION_RE.search(goal):
        blocked_note = (
            "Goal mentions filing/service/settlement/waiver language. "
            "OpenClaw will plan and analyze only — **no autonomous external actions**."
        )
    else:
        blocked_note = ""

    plan = plan_goal(goal)[: max(1, min(max_steps, 12))]
    steps: list[ClawStep] = []
    if execute:
        for item in plan:
            steps.append(_run_tool(item["tool_id"], goal, user, auto_approve=auto_approve))
    else:
        tools = _tool_map()
        for item in plan:
            t = tools.get(item["tool_id"])
            steps.append(
                ClawStep(
                    item["tool_id"],
                    item["title"],
                    "planned",
                    "Planned — not executed (execute=false).",
                    risk=t.risk if t else "low",
                )
            )

    # Compose summary
    ran = [s for s in steps if s.status == "ran"]
    need = [s for s in steps if s.status == "needs_approval"]
    parts = [
        "# OpenClaw agent run",
        f"**Goal:** {goal[:800]}",
        "",
        f"Steps: {len(steps)} · ran: {len(ran)} · needs approval: {len(need)}",
    ]
    if blocked_note:
        parts.extend(["", f"> {blocked_note}"])
    for s in steps:
        parts.append(f"\n## {s.title} (`{s.tool_id}` · {s.status})")
        if s.output:
            parts.append(s.output[:3000])
    parts.append(
        "\n---\n**Not legal advice.** OpenClaw harness is supervised. "
        "court_ready=false. Human owns filings and advice."
    )
    raw = "\n".join(parts)
    safe = enforce_output_safety(raw, mode="balanced")
    summary = safe.rewritten_content or raw

    run_id = f"claw_{uuid.uuid4().hex[:14]}"
    status = "needs_approval" if need else "completed"
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO openclaw_runs
            (run_id, org_id, user_id, goal, status, plan_json, steps_json, result_summary, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                user.org_id,
                user.user_id,
                goal[:4000],
                status,
                json.dumps(plan),
                json.dumps([s.to_dict() for s in steps]),
                summary[:50_000],
                now_iso(),
            ),
        )

    return {
        "run_id": run_id,
        "ok": True,
        "status": status,
        "goal": goal,
        "plan": plan,
        "steps": [s.to_dict() for s in steps],
        "summary": summary,
        "court_ready": False,
        "legal_advice": False,
        "openclaw": True,
        "inspired_by": "https://openclaw.ai/",
        "warnings": [
            "Supervised agent — no autonomous filing/service/settlement/waiver.",
            blocked_note,
        ]
        if blocked_note
        else ["Supervised agent — no autonomous filing/service/settlement/waiver."],
        "controls": {"court_ready": False, "legal_advice": False, "openclaw": True},
    }


def write_memory(
    user: UserInfo,
    *,
    key: str,
    value: str,
    tags: Optional[list[str]] = None,
) -> dict[str, Any]:
    _ensure()
    mid = f"mem_{uuid.uuid4().hex[:12]}"
    now = now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO openclaw_memory
            (memory_id, org_id, user_id, key, value, tags_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mid,
                user.org_id,
                user.user_id,
                key[:120],
                value[:4000],
                json.dumps(tags or []),
                now,
                now,
            ),
        )
    return {"memory_id": mid, "key": key, "ok": True}


def list_memory(user: UserInfo, *, limit: int = 20) -> list[dict[str, Any]]:
    _ensure()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT memory_id, key, value, tags_json, created_at, updated_at
            FROM openclaw_memory
            WHERE org_id = ? AND user_id = ?
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (user.org_id, user.user_id, max(1, min(limit, 100))),
        ).fetchall()
    out = []
    for r in rows:
        out.append(
            {
                "memory_id": r["memory_id"],
                "key": r["key"],
                "value": r["value"],
                "tags": json.loads(r["tags_json"] or "[]"),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
        )
    return out


def list_runs(user: UserInfo, *, limit: int = 10) -> list[dict[str, Any]]:
    _ensure()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT run_id, goal, status, created_at
            FROM openclaw_runs
            WHERE org_id = ? AND user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user.org_id, user.user_id, max(1, min(limit, 50))),
        ).fetchall()
    return [dict(r) for r in rows]


def capabilities() -> dict[str, Any]:
    return {
        "name": "OpenClaw Legal Harness",
        "inspired_by": "https://openclaw.ai/",
        "version": "1.0",
        "features": [
            "multi_step_planning",
            "tool_plugins",
            "session_memory",
            "human_approval_gates",
            "skill_pack_loading",
            "fail_closed_legal_actions",
        ],
        "blocked_autonomous_actions": [
            "file",
            "serve",
            "settle",
            "waive_privilege",
            "e-file",
        ],
        "tools": list_tools(),
        "court_ready_default": False,
        "legal_advice": False,
    }
