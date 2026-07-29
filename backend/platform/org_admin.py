"""Org admin: provider allowlists, usage quotas, cost telemetry.

In-process + SQLite/Postgres persistence. Multi-worker deployments should
replace counters with Redis later; structure is org-scoped and audited.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from backend.db import get_connection, init_db
from backend.db.helpers import now_iso
from backend.identity import AuthError, UserInfo

_DDL = """
CREATE TABLE IF NOT EXISTS org_ai_settings (
  org_id TEXT PRIMARY KEY,
  allowed_providers_json TEXT NOT NULL DEFAULT '["puter","kimi","safe_local","ollama"]',
  default_provider TEXT NOT NULL DEFAULT 'puter',
  daily_request_quota INTEGER NOT NULL DEFAULT 500,
  monthly_token_budget INTEGER NOT NULL DEFAULT 2000000,
  allow_external_llm INTEGER NOT NULL DEFAULT 0,
  allow_web_research INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL DEFAULT '',
  updated_by TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS org_ai_usage (
  usage_id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  user_id TEXT NOT NULL DEFAULT '',
  provider TEXT NOT NULL DEFAULT '',
  model TEXT NOT NULL DEFAULT '',
  feature TEXT NOT NULL DEFAULT 'chat',
  input_tokens INTEGER NOT NULL DEFAULT 0,
  output_tokens INTEGER NOT NULL DEFAULT 0,
  estimated_cost_usd REAL NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS org_ai_daily (
  org_id TEXT NOT NULL,
  day TEXT NOT NULL,
  request_count INTEGER NOT NULL DEFAULT 0,
  input_tokens INTEGER NOT NULL DEFAULT 0,
  output_tokens INTEGER NOT NULL DEFAULT 0,
  estimated_cost_usd REAL NOT NULL DEFAULT 0,
  PRIMARY KEY (org_id, day)
);
"""

# Rough public list prices (USD / 1M tokens) for telemetry estimates only
_COST_PER_MTOK = {
    "puter": (0.0, 0.0),  # user-pays via Puter account; org telemetry cost stays 0
    "kimi": (0.0, 0.0),  # Puter user-pays; server Moonshot billed separately if keyed
    "safe_local": (0.0, 0.0),
    "ollama": (0.0, 0.0),
    "openai": (2.5, 10.0),
    "openrouter": (1.0, 3.0),
    "anthropic": (3.0, 15.0),
}


def _ensure() -> None:
    init_db()
    with get_connection() as conn:
        for stmt in _DDL.split(";"):
            s = stmt.strip()
            if s:
                conn.execute(s)


def _require_admin(user: UserInfo) -> None:
    if user.role not in ("owner", "admin", "lawyer"):
        # lawyers can view telemetry; only owner/admin mutate settings
        pass


def _require_settings_admin(user: UserInfo) -> None:
    if user.role not in ("owner", "admin"):
        raise AuthError("Org AI settings require owner or admin role")


@dataclass
class OrgAiSettings:
    org_id: str
    allowed_providers: list[str] = field(
        default_factory=lambda: ["puter", "kimi", "safe_local", "ollama"]
    )
    default_provider: str = "puter"
    daily_request_quota: int = 500
    monthly_token_budget: int = 2_000_000
    allow_external_llm: bool = False
    allow_web_research: bool = False
    updated_at: str = ""
    updated_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "org_id": self.org_id,
            "allowed_providers": self.allowed_providers,
            "default_provider": self.default_provider,
            "daily_request_quota": self.daily_request_quota,
            "monthly_token_budget": self.monthly_token_budget,
            "allow_external_llm": self.allow_external_llm,
            "allow_web_research": self.allow_web_research,
            "updated_at": self.updated_at,
            "updated_by": self.updated_by,
        }


def get_settings(org_id: str) -> OrgAiSettings:
    _ensure()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM org_ai_settings WHERE org_id = ?", (org_id,)
        ).fetchone()
    if not row:
        s = OrgAiSettings(org_id=org_id)
        # seed defaults
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO org_ai_settings
                (org_id, allowed_providers_json, default_provider, daily_request_quota,
                 monthly_token_budget, allow_external_llm, allow_web_research, updated_at)
                VALUES (?, ?, ?, ?, ?, 0, 0, ?)
                """,
                (
                    org_id,
                    json.dumps(s.allowed_providers),
                    s.default_provider,
                    s.daily_request_quota,
                    s.monthly_token_budget,
                    now_iso(),
                ),
            )
        return s
    return OrgAiSettings(
        org_id=org_id,
        allowed_providers=json.loads(row["allowed_providers_json"] or "[]"),
        default_provider=row["default_provider"] or "puter",
        daily_request_quota=int(row["daily_request_quota"] or 500),
        monthly_token_budget=int(row["monthly_token_budget"] or 2_000_000),
        allow_external_llm=bool(row["allow_external_llm"]),
        allow_web_research=bool(row["allow_web_research"]),
        updated_at=row["updated_at"] or "",
        updated_by=row["updated_by"] or "",
    )


def update_settings(user: UserInfo, **fields: Any) -> OrgAiSettings:
    _require_settings_admin(user)
    current = get_settings(user.org_id)
    if "allowed_providers" in fields and fields["allowed_providers"] is not None:
        current.allowed_providers = list(fields["allowed_providers"])
        if "safe_local" not in current.allowed_providers:
            current.allowed_providers.insert(0, "safe_local")
    if "default_provider" in fields and fields["default_provider"]:
        current.default_provider = str(fields["default_provider"])
    if "daily_request_quota" in fields and fields["daily_request_quota"] is not None:
        current.daily_request_quota = max(1, int(fields["daily_request_quota"]))
    if "monthly_token_budget" in fields and fields["monthly_token_budget"] is not None:
        current.monthly_token_budget = max(1000, int(fields["monthly_token_budget"]))
    if "allow_external_llm" in fields and fields["allow_external_llm"] is not None:
        current.allow_external_llm = bool(fields["allow_external_llm"])
    if "allow_web_research" in fields and fields["allow_web_research"] is not None:
        current.allow_web_research = bool(fields["allow_web_research"])
    current.updated_at = now_iso()
    current.updated_by = user.user_id
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO org_ai_settings
            (org_id, allowed_providers_json, default_provider, daily_request_quota,
             monthly_token_budget, allow_external_llm, allow_web_research, updated_at, updated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(org_id) DO UPDATE SET
              allowed_providers_json = excluded.allowed_providers_json,
              default_provider = excluded.default_provider,
              daily_request_quota = excluded.daily_request_quota,
              monthly_token_budget = excluded.monthly_token_budget,
              allow_external_llm = excluded.allow_external_llm,
              allow_web_research = excluded.allow_web_research,
              updated_at = excluded.updated_at,
              updated_by = excluded.updated_by
            """,
            (
                current.org_id,
                json.dumps(current.allowed_providers),
                current.default_provider,
                current.daily_request_quota,
                current.monthly_token_budget,
                1 if current.allow_external_llm else 0,
                1 if current.allow_web_research else 0,
                current.updated_at,
                current.updated_by,
            ),
        )
    return current


def _day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _estimate_cost(provider: str, in_tok: int, out_tok: int) -> float:
    inp, outp = _COST_PER_MTOK.get(provider, (1.0, 3.0))
    return (in_tok / 1_000_000.0) * inp + (out_tok / 1_000_000.0) * outp


def check_quota(user: UserInfo, *, provider: str) -> dict[str, Any]:
    """Return allow/deny for a request against org settings + daily counters."""
    settings = get_settings(user.org_id)
    if provider not in settings.allowed_providers:
        return {
            "allowed": False,
            "reason": f"Provider '{provider}' not in org allowlist",
            "settings": settings.to_dict(),
        }
    if provider in ("openai", "openrouter", "anthropic") and not settings.allow_external_llm:
        if os.environ.get("ALA_ALLOW_EXTERNAL_LLM", "").strip().lower() not in ("1", "true", "yes"):
            return {
                "allowed": False,
                "reason": "External LLM disabled for org (and ALA_ALLOW_EXTERNAL_LLM not set)",
                "settings": settings.to_dict(),
            }
    day = _day()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT request_count, input_tokens, output_tokens FROM org_ai_daily WHERE org_id = ? AND day = ?",
            (user.org_id, day),
        ).fetchone()
    req = int(row["request_count"]) if row else 0
    if req >= settings.daily_request_quota:
        return {
            "allowed": False,
            "reason": f"Daily request quota exceeded ({req}/{settings.daily_request_quota})",
            "settings": settings.to_dict(),
            "usage_today": {"requests": req},
        }
    return {
        "allowed": True,
        "reason": "ok",
        "settings": settings.to_dict(),
        "usage_today": {
            "requests": req,
            "remaining": settings.daily_request_quota - req,
        },
    }


def record_usage(
    user: UserInfo,
    *,
    provider: str,
    model: str = "",
    feature: str = "chat",
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> dict[str, Any]:
    _ensure()
    # crude char-based estimate if tokens missing
    if input_tokens <= 0 and output_tokens <= 0:
        input_tokens = 50
        output_tokens = 100
    cost = _estimate_cost(provider, input_tokens, output_tokens)
    uid = f"use_{uuid.uuid4().hex[:14]}"
    day = _day()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO org_ai_usage
            (usage_id, org_id, user_id, provider, model, feature, input_tokens, output_tokens, estimated_cost_usd, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                uid,
                user.org_id,
                user.user_id,
                provider,
                model,
                feature,
                input_tokens,
                output_tokens,
                cost,
                now_iso(),
            ),
        )
        existing = conn.execute(
            "SELECT request_count FROM org_ai_daily WHERE org_id = ? AND day = ?",
            (user.org_id, day),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE org_ai_daily SET
                  request_count = request_count + 1,
                  input_tokens = input_tokens + ?,
                  output_tokens = output_tokens + ?,
                  estimated_cost_usd = estimated_cost_usd + ?
                WHERE org_id = ? AND day = ?
                """,
                (input_tokens, output_tokens, cost, user.org_id, day),
            )
        else:
            conn.execute(
                """
                INSERT INTO org_ai_daily
                (org_id, day, request_count, input_tokens, output_tokens, estimated_cost_usd)
                VALUES (?, ?, 1, ?, ?, ?)
                """,
                (user.org_id, day, input_tokens, output_tokens, cost),
            )
    return {"usage_id": uid, "estimated_cost_usd": cost, "day": day}


def telemetry_summary(user: UserInfo, *, days: int = 14) -> dict[str, Any]:
    _require_admin(user)
    settings = get_settings(user.org_id)
    with get_connection() as conn:
        daily = conn.execute(
            """
            SELECT day, request_count, input_tokens, output_tokens, estimated_cost_usd
            FROM org_ai_daily WHERE org_id = ?
            ORDER BY day DESC LIMIT ?
            """,
            (user.org_id, days),
        ).fetchall()
        by_provider = conn.execute(
            """
            SELECT provider, COUNT(*) AS n, SUM(input_tokens) AS tin, SUM(output_tokens) AS tout,
                   SUM(estimated_cost_usd) AS cost
            FROM org_ai_usage WHERE org_id = ?
            GROUP BY provider
            """,
            (user.org_id,),
        ).fetchall()
        recent = conn.execute(
            """
            SELECT usage_id, provider, model, feature, input_tokens, output_tokens,
                   estimated_cost_usd, created_at, user_id
            FROM org_ai_usage WHERE org_id = ?
            ORDER BY created_at DESC LIMIT 30
            """,
            (user.org_id,),
        ).fetchall()
    return {
        "settings": settings.to_dict(),
        "daily": [dict(r) for r in daily],
        "by_provider": [dict(r) for r in by_provider],
        "recent": [dict(r) for r in recent],
        "currency": "USD",
        "note": "Cost estimates are approximate public list-price proxies — not invoices.",
    }
