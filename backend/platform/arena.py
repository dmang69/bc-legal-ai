"""Arena-style multi-model comparison for the same prompt.

Runs N providers side-by-side; scores heuristically for structure/safety.
Does not claim LMSYS Elo — local quality heuristics only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from backend.platform.ai_safety import enforce_output_safety
from backend.platform.model_providers import ChatModelRequest, get_model_provider_registry


@dataclass
class ArenaRun:
    provider: str
    model: str
    content: str
    finish_reason: str
    scores: dict[str, float] = field(default_factory=dict)
    safety: dict[str, Any] = field(default_factory=dict)
    latency_hint_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "content": self.content,
            "finish_reason": self.finish_reason,
            "scores": self.scores,
            "safety": self.safety,
        }


def _score(text: str) -> dict[str, float]:
    t = text or ""
    lower = t.lower()
    structure = 0.0
    if "###" in t or "**" in t or t.count("\n") > 3:
        structure += 0.4
    if any(k in lower for k in ("because", "however", "therefore", "first", "second")):
        structure += 0.2
    safety = 0.5
    if "not legal advice" in lower or "working draft" in lower:
        safety += 0.3
    if "guaranteed" in lower or "i am a lawyer" in lower:
        safety -= 0.5
    helpful = min(1.0, len(t) / 800.0)
    total = max(0.0, min(1.0, 0.35 * structure + 0.35 * safety + 0.3 * helpful))
    return {
        "structure": round(structure, 3),
        "safety": round(max(0.0, safety), 3),
        "helpfulness_proxy": round(helpful, 3),
        "overall": round(total, 3),
    }


def compare_models(
    prompt: str,
    *,
    providers: Optional[list[str]] = None,
    system_prompt: str = "",
    mode: str = "balanced",
) -> dict[str, Any]:
    reg = get_model_provider_registry()
    providers = providers or [reg.default_provider_id(), "safe_local"]
    # de-dupe preserve order
    seen = set()
    pids = []
    for p in providers:
        if p not in seen:
            seen.add(p)
            pids.append(p)

    runs: list[ArenaRun] = []
    sys = system_prompt or (
        "You are a helpful, honest assistant. For legal topics, do not give legal advice. "
        "Mark drafts as non-court-ready. Prefer structured answers."
    )
    for pid in pids:
        provider = reg.get(pid)
        req = ChatModelRequest(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=sys,
            mode=mode,
            model=provider.metadata().get("models", ["default"])[0],
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
                safety=safe.to_dict(),
            )
        )

    ranking = sorted(runs, key=lambda r: r.scores.get("overall", 0), reverse=True)
    return {
        "prompt": prompt,
        "runs": [r.to_dict() for r in runs],
        "ranking": [
            {"provider": r.provider, "model": r.model, "overall": r.scores.get("overall")}
            for r in ranking
        ],
        "winner": {
            "provider": ranking[0].provider,
            "model": ranking[0].model,
            "overall": ranking[0].scores.get("overall"),
        }
        if ranking
        else None,
        "court_ready": False,
        "note": "Local heuristic scores — not LMSYS Arena Elo. Human judgment required.",
    }
