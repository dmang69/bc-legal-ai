"""Structured feature options catalog for BC Legal AI Platform.

Single source of truth for product capabilities: install surfaces, AI pillars,
legal tools, productivity, and governance. Used by suite API, org admin, and UI.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class FeatureOption:
    id: str
    name: str
    category: str  # install | ai | legal | productivity | governance | client
    description: str
    status: str  # live | partial | target
    default_enabled: bool = True
    org_toggleable: bool = False  # can org admin turn off?
    env_gate: str = ""  # env var that must be truthy if gated
    endpoints: list[str] = field(default_factory=list)
    providers: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)  # windows|macos|linux|android|ios|chrome|api
    safety_locks: list[str] = field(default_factory=list)
    docs: str = ""

    def to_dict(self, *, enabled: Optional[bool] = None) -> dict[str, Any]:
        d = asdict(self)
        d["enabled"] = self.default_enabled if enabled is None else enabled
        return d


# --- Catalog (stable IDs — do not rename without migration) ---

FEATURE_CATALOG: list[FeatureOption] = [
    # Install / clients
    FeatureOption(
        id="client.windows_setup",
        name="Windows Setup (.exe / MSI)",
        category="install",
        description="NSIS Setup and MSI Workbench installers with in-place upgrade (same product id).",
        status="live",
        platforms=["windows"],
        docs="INSTALL.md#2-windows--exe-setup-installer-workbench",
        safety_locks=["unsigned_dev_only_until_authenticode"],
    ),
    FeatureOption(
        id="client.macos",
        name="macOS (.dmg / .app)",
        category="install",
        description="Tauri macOS Workbench package; notarize before public distribution.",
        status="partial",
        platforms=["macos"],
        docs="INSTALL.md#3-macos--dmg--app",
    ),
    FeatureOption(
        id="client.linux",
        name="Linux (Docker / AppImage)",
        category="install",
        description="API via Docker; optional Tauri desktop bundle on Linux hosts.",
        status="live",
        platforms=["linux", "api"],
        docs="INSTALL.md#4-linux--desktop--server",
    ),
    FeatureOption(
        id="client.android",
        name="Android (Play .aab / APK)",
        category="install",
        description="Tauri Android Client; store upgrades via versionCode.",
        status="partial",
        platforms=["android"],
        docs="INSTALL.md#5-android--google-play--apk",
    ),
    FeatureOption(
        id="client.ios",
        name="iPhone / iPad (TestFlight)",
        category="install",
        description="Tauri iOS Client; App Store / TestFlight build numbers.",
        status="partial",
        platforms=["ios"],
        docs="INSTALL.md#6-iphone--ipad--testflight--app-store",
    ),
    FeatureOption(
        id="client.chrome_pwa",
        name="Google Chrome / Edge PWA",
        category="install",
        description="Install Portal as app via web app manifest (HTTPS required).",
        status="live",
        platforms=["chrome"],
        docs="INSTALL.md#1-google-chrome--edge--desktop-browser-pwa-portal",
    ),
    FeatureOption(
        id="client.desktop_autoupdate",
        name="Desktop auto-updater",
        category="install",
        description="Tauri updater via GitHub Releases latest.json (minisign).",
        status="partial",
        platforms=["windows", "macos", "linux"],
        docs="docs/UPGRADES.md",
        safety_locks=["requires_release_signing_key"],
    ),
    # AI pillars
    FeatureOption(
        id="ai.puter_base",
        name="Puter AI base",
        category="ai",
        description="Default browser AI gateway (500+ models, user-pays, no server API keys).",
        status="live",
        org_toggleable=True,
        providers=["puter"],
        endpoints=["/v1/platform/conversations/{id}/messages"],
        platforms=["chrome", "windows", "macos", "linux", "api"],
        docs="https://developer.puter.com/ai/",
        safety_locks=["client_side", "output_safety_gate", "court_ready_false"],
    ),
    FeatureOption(
        id="ai.kimi",
        name="Kimi (Moonshot) long-context",
        category="ai",
        description="Long-context deep analysis via Puter model moonshotai/kimi-k2.5.",
        status="live",
        org_toggleable=True,
        providers=["kimi"],
        platforms=["chrome", "windows", "macos", "api"],
        docs="docs/ENTERPRISE_AI_SUITE.md",
        safety_locks=["client_side", "output_safety_gate"],
    ),
    FeatureOption(
        id="ai.openclaw",
        name="OpenClaw agent harness",
        category="ai",
        description="Multi-step plans, tool plugins, memory, HITL — no autonomous filing.",
        status="live",
        org_toggleable=True,
        endpoints=[
            "/v1/platform/ai/openclaw/run",
            "/v1/platform/ai/openclaw/tools",
            "/v1/platform/ai/openclaw/capabilities",
        ],
        platforms=["api", "chrome", "windows", "macos"],
        docs="https://openclaw.ai/",
        safety_locks=["no_autonomous_file_serve_settle", "hitl_high_risk"],
    ),
    FeatureOption(
        id="ai.arena",
        name="Arena AI comparison",
        category="ai",
        description="Side-by-side multi-model evaluation with legal-aware heuristic scores.",
        status="live",
        org_toggleable=True,
        endpoints=["/v1/platform/ai/arena", "/v1/platform/ai/arena/presets"],
        platforms=["api", "chrome", "windows", "macos"],
        docs="docs/ENTERPRISE_AI_SUITE.md",
        safety_locks=["not_lmsys_elo", "court_ready_false"],
    ),
    FeatureOption(
        id="ai.ollama_local",
        name="Ollama local models",
        category="ai",
        description="Private local inference; preferred for private_local mode.",
        status="live",
        org_toggleable=True,
        env_gate="",
        providers=["ollama"],
        platforms=["windows", "macos", "linux", "api"],
        docs="docs/ENTERPRISE_AI_SUITE.md",
        safety_locks=["local_network"],
    ),
    FeatureOption(
        id="ai.safe_local",
        name="Safe local orchestrator",
        category="ai",
        description="Deterministic offline fallback (no external model egress).",
        status="live",
        default_enabled=True,
        org_toggleable=False,  # always available as fail-safe
        providers=["safe_local"],
        platforms=["api"],
        safety_locks=["always_on_failsafe"],
    ),
    FeatureOption(
        id="ai.external_cloud_llm",
        name="External cloud LLMs (OpenAI / Anthropic / OpenRouter)",
        category="ai",
        description="Server-side cloud providers; require privacy review and explicit enable.",
        status="live",
        default_enabled=False,
        org_toggleable=True,
        env_gate="ALA_ALLOW_EXTERNAL_LLM",
        providers=["openai", "anthropic", "openrouter"],
        platforms=["api"],
        safety_locks=["fail_closed_default", "org_flag_required"],
    ),
    # Legal
    FeatureOption(
        id="legal.jr_clock",
        name="JR limitation clock (ATA s.57)",
        category="legal",
        description="Deterministic 60-day JR clock with alternatives when uncertain; HITL labeling.",
        status="live",
        endpoints=[],
        platforms=["api", "chrome"],
        safety_locks=["not_filing_advice", "hitl_required"],
    ),
    FeatureOption(
        id="legal.citations",
        name="Citation fail-closed gates",
        category="legal",
        description="Reject incorrect section mappings; never invent court-ready authorities.",
        status="live",
        platforms=["api"],
        safety_locks=["court_ready_false"],
    ),
    FeatureOption(
        id="legal.form66",
        name="Form 66 / 67 scaffolding",
        category="legal",
        description="Petition (66) vs response (67) awareness in skills and drafting outlines.",
        status="live",
        platforms=["api"],
    ),
    FeatureOption(
        id="legal.skills_packs",
        name="In-repo legal skill packs",
        category="legal",
        description="RTB / JR / advocacy markdown operating procedures loaded into context.",
        status="live",
        platforms=["api"],
    ),
    FeatureOption(
        id="legal.matter_acl",
        name="Matter ACL & ethical walls",
        category="legal",
        description="Org/matter isolation; no cross-matter ambient authority.",
        status="live",
        org_toggleable=False,
        platforms=["api"],
        safety_locks=["always_on"],
    ),
    FeatureOption(
        id="legal.hearing_prep",
        name="Tribunal hearing preparation",
        category="legal",
        description=(
            "Structured prep: dissect record, legal test, tabbed binders, "
            "opening/submissions, witness coaching, Q&A simulation (RTB/BCHRT/JR)."
        ),
        status="live",
        org_toggleable=True,
        endpoints=[],
        platforms=["api", "chrome", "windows", "macos"],
        docs="skills/tribunal-hearing-prep/SKILL.md",
        safety_locks=["not_legal_advice", "no_false_testimony", "hitl_strategy"],
    ),
    # Productivity
    FeatureOption(
        id="prod.summarize",
        name="Summarize",
        category="productivity",
        description="Extractive summaries via /summarize and API.",
        status="live",
        endpoints=["/v1/platform/ai/summarize"],
        platforms=["api", "chrome"],
    ),
    FeatureOption(
        id="prod.email",
        name="Email draft",
        category="productivity",
        description="Professional email draft scaffolds.",
        status="live",
        endpoints=["/v1/platform/ai/email-draft"],
        platforms=["api", "chrome"],
    ),
    FeatureOption(
        id="prod.research_plan",
        name="Research plan",
        category="productivity",
        description="Structured research planning for legal issues.",
        status="live",
        endpoints=["/v1/platform/ai/creative"],  # research via chat /research
        platforms=["api", "chrome"],
    ),
    FeatureOption(
        id="prod.code",
        name="Code assist",
        category="productivity",
        description="Complete / debug / document helpers.",
        status="live",
        endpoints=["/v1/platform/ai/code"],
        platforms=["api", "chrome"],
    ),
    FeatureOption(
        id="prod.web_research",
        name="Allowlisted web research",
        category="productivity",
        description="Bounded public/official link research; off by default.",
        status="live",
        default_enabled=False,
        org_toggleable=True,
        env_gate="ALA_WEB_RESEARCH",
        endpoints=["/v1/platform/ai/web-research"],
        platforms=["api"],
        safety_locks=["host_allowlist", "court_ready_false"],
    ),
    # Governance
    FeatureOption(
        id="gov.auth",
        name="Org auth (register / login)",
        category="governance",
        description="Bearer + session/CSRF patterns for platform access.",
        status="live",
        org_toggleable=False,
        platforms=["api"],
        safety_locks=["always_on"],
    ),
    FeatureOption(
        id="gov.audit",
        name="Hash-chained audit ledger",
        category="governance",
        description="Append-only audit events for sensitive actions.",
        status="live",
        org_toggleable=False,
        platforms=["api"],
        safety_locks=["always_on"],
    ),
    FeatureOption(
        id="gov.quotas",
        name="Org AI quotas & telemetry",
        category="governance",
        description="Daily request quotas, provider allowlists, usage estimates.",
        status="live",
        org_toggleable=False,
        endpoints=["/v1/platform/org/ai/settings", "/v1/platform/org/ai/telemetry"],
        platforms=["api"],
    ),
    FeatureOption(
        id="gov.court_ready_fail_closed",
        name="Court-ready fail-closed",
        category="governance",
        description="Outputs never court_ready without full human export gates.",
        status="live",
        default_enabled=True,
        org_toggleable=False,
        platforms=["api"],
        safety_locks=["always_on", "not_legal_advice"],
    ),
]


def _env_truthy(name: str) -> bool:
    if not name:
        return True
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def resolve_feature_enabled(
    feat: FeatureOption,
    *,
    org_enabled: Optional[dict[str, bool]] = None,
    allowed_providers: Optional[list[str]] = None,
    allow_external_llm: bool = False,
    allow_web_research: bool = False,
) -> bool:
    """Compute effective enabled flag for a feature."""
    org_enabled = org_enabled or {}
    allowed_providers = allowed_providers or []

    if feat.id == "gov.court_ready_fail_closed" or feat.id == "ai.safe_local":
        return True
    if feat.id == "legal.matter_acl" or feat.id == "gov.auth" or feat.id == "gov.audit":
        return True

    if feat.env_gate and not _env_truthy(feat.env_gate):
        # org may still want the flag, but env blocks external
        if feat.id == "ai.external_cloud_llm":
            return False
        if feat.id == "prod.web_research" and not allow_web_research:
            return False

    if feat.id == "ai.external_cloud_llm":
        return allow_external_llm and _env_truthy("ALA_ALLOW_EXTERNAL_LLM")

    if feat.id == "prod.web_research":
        return allow_web_research or _env_truthy("ALA_WEB_RESEARCH")

    # Provider-linked features respect org allowlist when toggleable
    if feat.providers and feat.org_toggleable:
        if allowed_providers and not any(p in allowed_providers for p in feat.providers):
            return False

    if feat.org_toggleable and feat.id in org_enabled:
        return bool(org_enabled[feat.id])

    return feat.default_enabled


def list_feature_options(
    *,
    org_enabled: Optional[dict[str, bool]] = None,
    allowed_providers: Optional[list[str]] = None,
    allow_external_llm: bool = False,
    allow_web_research: bool = False,
    category: str = "",
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for feat in FEATURE_CATALOG:
        if category and feat.category != category:
            continue
        enabled = resolve_feature_enabled(
            feat,
            org_enabled=org_enabled,
            allowed_providers=allowed_providers,
            allow_external_llm=allow_external_llm,
            allow_web_research=allow_web_research,
        )
        out.append(feat.to_dict(enabled=enabled))
    return out


def feature_categories() -> list[dict[str, str]]:
    return [
        {"id": "install", "label": "Install & clients", "description": "Windows, macOS, Linux, mobile, Chrome PWA"},
        {"id": "ai", "label": "AI suite", "description": "Puter, Kimi, OpenClaw, Arena, Ollama, cloud LLMs"},
        {"id": "legal", "label": "Legal tooling", "description": "JR clock, citations, Form 66, skills, ACL"},
        {"id": "productivity", "label": "Productivity", "description": "Summarize, email, research, code, web"},
        {"id": "governance", "label": "Governance & safety", "description": "Auth, audit, quotas, court_ready locks"},
    ]


def features_manifest(
    *,
    org_enabled: Optional[dict[str, bool]] = None,
    allowed_providers: Optional[list[str]] = None,
    allow_external_llm: bool = False,
    allow_web_research: bool = False,
) -> dict[str, Any]:
    features = list_feature_options(
        org_enabled=org_enabled,
        allowed_providers=allowed_providers,
        allow_external_llm=allow_external_llm,
        allow_web_research=allow_web_research,
    )
    by_cat: dict[str, list[dict[str, Any]]] = {}
    for f in features:
        by_cat.setdefault(f["category"], []).append(f)
    return {
        "product": "BC Legal AI Associate",
        "version": "1.0",
        "court_ready_default": False,
        "legal_advice": False,
        "categories": feature_categories(),
        "features": features,
        "by_category": by_cat,
        "selection_guide": {
            "pilot_synthetic": [
                "ai.puter_base",
                "ai.safe_local",
                "ai.openclaw",
                "ai.arena",
                "legal.jr_clock",
                "legal.citations",
                "legal.hearing_prep",
                "gov.court_ready_fail_closed",
            ],
            "hearing_prep_rtb_jr": [
                "legal.hearing_prep",
                "legal.jr_clock",
                "legal.citations",
                "legal.form66",
                "legal.skills_packs",
                "ai.openclaw",
                "gov.court_ready_fail_closed",
            ],
            "private_sensitive": [
                "ai.ollama_local",
                "ai.safe_local",
                "legal.matter_acl",
                "gov.audit",
            ],
            "full_desktop": [
                "client.windows_setup",
                "client.macos",
                "client.chrome_pwa",
                "client.desktop_autoupdate",
            ],
        },
        "locks": [
            "not_legal_advice",
            "court_ready_false_default",
            "no_autonomous_filing",
            "external_llm_fail_closed",
        ],
    }
