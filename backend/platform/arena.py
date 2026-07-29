"""Arena AI — multi-model comparison and ranking.

Side-by-side provider runs with legal-aware heuristic scores.
Not LMSYS Elo — local quality heuristics + optional client-side Puter/Kimi runs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from backend.platform.ai_safety import enforce_output_safety
from backend.platform.model_providers import ChatModelRequest, get_model_provider_registry

# Named lineups for one-click Arena AI
ARENA_PRESETS: dict[str, dict[str, Any]] = {
    "legal_core": {
        "id": "legal_core",
        "label": "Legal core",
        "description": "Safe local + Kimi + Puter baseline",
        "providers": ["safe_local", "kimi", "puter"],
    },
    "private": {
        "id": "private",
        "label": "Private local",
        "description": "Safe local + Ollama only",
        "providers": ["safe_local", "ollama"],
    },
    "frontier": {
        "id": "frontier",
        "label": "Frontier mix",
        "description": "Puter, Kimi, OpenAI, Anthropic (keys/gates apply)",
        "providers": ["puter", "kimi", "openai", "anthropic", "safe_local"],
    },
    "kimi_focus": {
        "id": "kimi_focus",
        "label": "Kimi deep",
        "description": "Kimi vs safe local vs Puter nano",
        "providers": ["kimi", "safe_local", "puter"],
    },
}


@dataclass
class ArenaRun:
    provider: str
    model: str
    content: str
    finish_reason: str
    scores: dict[str, float] = field(default_factory=dict)
    safety: dict[str, Any] = field(default_factory=dict)
    latency_hint_ms: int = 0
    source: str = "server"  # server | client

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "content": self.content,
            "finish_reason": self.finish_reason,
            "scores": self.scores,
            "safety": self.safety,
            "latency_hint_ms": self.latency_hint_ms,
            "source": self.source,
        }


def _score(text: str) -> dict[str, float]:
    """Legal-aware local heuristics (not public Elo)."""
    t = text or ""
    lower = t.lower()
    structure = 0.0
    if "###" in t or "**" in t or t.count("\n") > 3:
        structure += 0.35
    if any(k in lower for k in ("because", "however", "therefore", "first", "second", "ground")):
        structure += 0.2
    if any(k in lower for k in ("issue", "analysis", "conclusion", "next steps")):
        structure += 0.15

    safety = 0.45
    if "not legal advice" in lower or "working draft" in lower or "court_ready" in lower:
        safety += 0.35
    if "human" in lower and ("review" in lower or "confirm" in lower or "supervision" in lower):
        safety += 0.1
    if "guaranteed" in lower or "i am a lawyer" in lower or "this is legal advice" in lower:
        safety -= 0.55
    if "file this today" in lower or "definitely win" in lower:
        safety -= 0.3

    # Citation hygiene: prefer caution over invented-looking precision without gate language
    citation = 0.4
    if "verify" in lower or "canlii" in lower or "bc laws" in lower or "pinpoint" in lower:
        citation += 0.3
    if re_has_bare_scc(lower) and "verify" not in lower:
        citation -= 0.15

    helpful = min(1.0, len(t) / 900.0)
    completeness = 0.3
    if len(t) > 200:
        completeness += 0.2
    if len(t) > 600:
        completeness += 0.2
    if any(k in lower for k in ("missing", "gap", "next", "checklist", "evidence")):
        completeness += 0.15

    total = max(
        0.0,
        min(
            1.0,
            0.22 * structure
            + 0.28 * max(0.0, safety)
            + 0.18 * max(0.0, citation)
            + 0.17 * helpful
            + 0.15 * min(1.0, completeness),
        ),
    )
    return {
        "structure": round(min(1.0, structure), 3),
        "safety": round(max(0.0, min(1.0, safety)), 3),
        "citation_hygiene": round(max(0.0, min(1.0, citation)), 3),
        "helpfulness_proxy": round(helpful, 3),
        "completeness": round(min(1.0, completeness), 3),
        "overall": round(total, 3),
    }


def re_has_bare_scc(lower: str) -> bool:
    import re

    return bool(re.search(r"\b\d{4}\s+scc\s+\d+\b", lower))


def list_presets() -> list[dict[str, Any]]:
    return list(ARENA_PRESETS.values())


def compare_models(
    prompt: str,
    *,
    providers: Optional[list[str]] = None,
    system_prompt: str = "",
    mode: str = "balanced",
    preset: str = "",
    client_runs: Optional[list[dict[str, Any]]] = None,
    models: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Run server providers + merge optional client-side Puter/Kimi results."""
    reg = get_model_provider_registry()
    models = models or {}

    if preset and preset in ARENA_PRESETS:
        providers = list(ARENA_PRESETS[preset]["providers"])
    providers = providers or [reg.default_provider_id(), "kimi", "safe_local"]

    seen: set[str] = set()
    pids: list[str] = []
    for p in providers:
        if p not in seen:
            seen.add(p)
            pids.append(p)

    # Client-side providers already executed in browser — skip server stub
    client_by_provider = {
        str(r.get("provider")): r
        for r in (client_runs or [])
        if isinstance(r, dict) and r.get("provider") and r.get("content")
    }

    runs: list[ArenaRun] = []
    sys = system_prompt or (
        "You are a helpful, honest assistant. For legal topics, do not give legal advice. "
        "Mark drafts as non-court-ready. Prefer structured answers with verification steps."
    )

    for pid in pids:
        if pid in client_by_provider:
            cr = client_by_provider[pid]
            content_raw = str(cr.get("content") or "")
            safe = enforce_output_safety(content_raw, mode=mode)
            content = safe.rewritten_content or content_raw
            runs.append(
                ArenaRun(
                    provider=pid,
                    model=str(cr.get("model") or models.get(pid) or "client"),
                    content=content,
                    finish_reason=str(cr.get("finish_reason") or "stop"),
                    scores=_score(content),
                    safety=safe.to_dict() if hasattr(safe, "to_dict") else {"court_ready": False},
                    latency_hint_ms=int(cr.get("latency_ms") or 0),
                    source="client",
                )
            )
            continue

        provider = reg.get(pid)
        meta = provider.metadata()
        # Prefer explicit model map, else provider default_model, else first model
        model = (
            models.get(pid)
            or meta.get("default_model")
            or (meta.get("models") or ["default"])[0]
        )
        req = ChatModelRequest(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=sys,
            mode=mode,
            model=str(model),
        )
        resp = provider.complete(req)
        safe = enforce_output_safety(resp.content, mode=mode)
        content = safe.rewritten_content or resp.content
        runs.append(
            ArenaRun(
                provider=resp.provider,
                model=resp.model,
                content=content,
                finish_reason=resp.finish_reason,
                scores=_score(content),
                safety=safe.to_dict() if hasattr(safe, "to_dict") else {"court_ready": False},
                source="server",
            )
        )

    # Extra client runs not in provider list
    for pid, cr in client_by_provider.items():
        if any(r.provider == pid for r in runs):
            continue
        content_raw = str(cr.get("content") or "")
        safe = enforce_output_safety(content_raw, mode=mode)
        content = safe.rewritten_content or content_raw
        runs.append(
            ArenaRun(
                provider=pid,
                model=str(cr.get("model") or "client"),
                content=content,
                finish_reason="stop",
                scores=_score(content),
                safety={"court_ready": False},
                source="client",
            )
        )

    ranking = sorted(runs, key=lambda r: r.scores.get("overall", 0), reverse=True)
    dimensions = ["structure", "safety", "citation_hygiene", "helpfulness_proxy", "completeness", "overall"]
    return {
        "prompt": prompt,
        "preset": preset or None,
        "runs": [r.to_dict() for r in runs],
        "ranking": [
            {
                "provider": r.provider,
                "model": r.model,
                "overall": r.scores.get("overall"),
                "source": r.source,
            }
            for r in ranking
        ],
        "winner": {
            "provider": ranking[0].provider,
            "model": ranking[0].model,
            "overall": ranking[0].scores.get("overall"),
            "source": ranking[0].source,
        }
        if ranking
        else None,
        "score_dimensions": dimensions,
        "presets_available": list(ARENA_PRESETS.keys()),
        "court_ready": False,
        "legal_advice": False,
        "arena_ai": True,
        "note": (
            "Arena AI local heuristic scores — not LMSYS Elo. "
            "Client-side Puter/Kimi runs merge when supplied. Human judgment required."
        ),
    }
