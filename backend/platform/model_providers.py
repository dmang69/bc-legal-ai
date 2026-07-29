"""Model provider abstraction — multi-vendor enterprise gateway.

Default AI base: Puter (browser Puter.js — user-pays, no server API keys).
  Docs: https://developer.puter.com/ai/

Also available:
  - safe_local: deterministic local orchestrator (no external egress)
  - ollama (ALA_OLLAMA_URL, default http://127.0.0.1:11434)
  - openai-compatible (OPENAI_API_KEY + OPENAI_BASE_URL)
  - anthropic (ANTHROPIC_API_KEY)

All responses should be passed through ai_safety.enforce_output_safety by callers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol


@dataclass(frozen=True)
class ChatModelRequest:
    messages: list[dict[str, str]]
    system_prompt: str = ""
    model: str = "safe-orchestrator"
    mode: str = "balanced"
    temperature: float = 0.2
    max_tokens: int = 2048
    tools: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ChatModelResponse:
    content: str
    provider: str
    model: str
    finish_reason: str = "stop"
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)
    safety: dict[str, Any] = field(default_factory=dict)


class ModelProvider(Protocol):
    provider_id: str

    def metadata(self) -> dict[str, Any]:
        ...

    def complete(self, request: ChatModelRequest) -> ChatModelResponse:
        ...


def _messages_with_system(request: ChatModelRequest) -> list[dict[str, str]]:
    msgs: list[dict[str, str]] = []
    if request.system_prompt:
        msgs.append({"role": "system", "content": request.system_prompt})
    msgs.extend(request.messages)
    return msgs


class SafeLocalProvider:
    provider_id = "safe_local"

    def metadata(self) -> dict[str, Any]:
        return {
            "id": self.provider_id,
            "name": "Safe Local Orchestrator",
            "configured": True,
            "external_network": False,
            "local": True,
            "models": ["safe-orchestrator"],
            "supports_streaming": True,
            "supports_tools": True,
            "default": False,
            "family": "deterministic",
        }

    def complete(self, request: ChatModelRequest) -> ChatModelResponse:
        last = next(
            (m.get("content", "") for m in reversed(request.messages) if m.get("role") == "user"),
            "",
        )
        history_n = len(request.messages)
        content = (
            "I can help in a supervised, multi-turn workspace with in-session memory of this chat.\n\n"
            f"**Your message:** {last[:1500]}\n\n"
            f"**Context:** {history_n} message(s) in request · mode=`{request.mode}`.\n\n"
            "I will keep legal outputs **non-court-ready** until citations, evidence, privilege, "
            "and human approval gates complete. Not legal advice.\n\n"
            "Available suite: summarize · email draft · research plan · code assist · "
            "local Ollama · model arena · optional live web (allowlisted)."
        )
        return ChatModelResponse(
            content=content,
            provider=self.provider_id,
            model=request.model or "safe-orchestrator",
            usage={
                "input_messages": history_n,
                "output_chars": len(content),
            },
            safety={
                "court_ready": False,
                "legal_advice": False,
                "external_network": False,
            },
        )


class OllamaProvider:
    """Run open-source models via local Ollama HTTP API."""

    provider_id = "ollama"

    def __init__(self) -> None:
        self.base_url = os.environ.get("ALA_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
        self.default_model = os.environ.get("ALA_OLLAMA_MODEL", "llama3.2")

    def metadata(self) -> dict[str, Any]:
        return {
            "id": self.provider_id,
            "name": "Ollama (local)",
            "configured": True,  # endpoint may be down; complete() handles
            "external_network": False,
            "local": True,
            "models": [self.default_model, "qwen2.5", "mistral", "codellama"],
            "supports_streaming": True,
            "supports_tools": False,
            "default": False,
            "base_url": self.base_url,
            "family": "ollama",
        }

    def complete(self, request: ChatModelRequest) -> ChatModelResponse:
        model = request.model if request.model and request.model != "safe-orchestrator" else self.default_model
        try:
            import httpx
        except ImportError:
            return ChatModelResponse(
                content="httpx required for Ollama. pip install httpx",
                provider=self.provider_id,
                model=model,
                finish_reason="dependency_missing",
            )
        payload = {
            "model": model,
            "messages": _messages_with_system(request),
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }
        try:
            with httpx.Client(timeout=120.0) as client:
                r = client.post(f"{self.base_url}/api/chat", json=payload)
                r.raise_for_status()
                data = r.json()
            content = (data.get("message") or {}).get("content") or data.get("response") or ""
            return ChatModelResponse(
                content=content,
                provider=self.provider_id,
                model=model,
                usage={
                    "eval_count": data.get("eval_count") or 0,
                    "prompt_eval_count": data.get("prompt_eval_count") or 0,
                },
                safety={"court_ready": False, "legal_advice": False, "external_network": False, "local": True},
            )
        except Exception as e:
            return ChatModelResponse(
                content=(
                    f"Ollama unavailable at {self.base_url}: {e}. "
                    "Install Ollama, pull a model (`ollama pull llama3.2`), and retry. "
                    "Falling back guidance: use provider `safe_local` or configure OPENAI_API_KEY."
                ),
                provider=self.provider_id,
                model=model,
                finish_reason="ollama_unreachable",
                safety={"court_ready": False, "external_network": False, "local": True},
            )


class OpenAICompatibleProvider:
    """OpenAI Chat Completions API (also works with Azure/OpenRouter-compatible bases)."""

    provider_id = "openai"

    def __init__(
        self,
        provider_id: str = "openai",
        name: str = "OpenAI-compatible",
        env_key: str = "OPENAI_API_KEY",
        base_env: str = "OPENAI_BASE_URL",
        default_base: str = "https://api.openai.com/v1",
        models: Optional[list[str]] = None,
    ) -> None:
        self.provider_id = provider_id
        self._name = name
        self._env_key = env_key
        self._base_env = base_env
        self._default_base = default_base
        self._models = models or ["gpt-4o-mini", "gpt-4o", "gpt-4.1"]

    def metadata(self) -> dict[str, Any]:
        return {
            "id": self.provider_id,
            "name": self._name,
            "configured": bool(os.getenv(self._env_key)),
            "external_network": True,
            "local": False,
            "models": self._models,
            "supports_streaming": True,
            "supports_tools": False,
            "default": False,
            "env_var": self._env_key,
            "base_url_env": self._base_env,
            "family": "openai_compatible",
        }

    def complete(self, request: ChatModelRequest) -> ChatModelResponse:
        key = os.getenv(self._env_key, "").strip()
        model = request.model if request.model and request.model != "safe-orchestrator" else self._models[0]
        if not key:
            return ChatModelResponse(
                content=(
                    f"{self._name} not configured. Set {self._env_key} after privacy review. "
                    "Prefer Ollama for private local inference."
                ),
                provider=self.provider_id,
                model=model,
                finish_reason="provider_unconfigured",
                safety={"court_ready": False, "external_network": True},
            )
        if os.environ.get("ALA_ALLOW_EXTERNAL_LLM", "").strip().lower() not in ("1", "true", "yes"):
            return ChatModelResponse(
                content=(
                    f"{self._name} key is present but external LLM calls are gated. "
                    "Set ALA_ALLOW_EXTERNAL_LLM=1 to enable live inference after compliance review."
                ),
                provider=self.provider_id,
                model=model,
                finish_reason="external_gated",
                safety={"court_ready": False, "external_network": True, "gated": True},
            )
        try:
            import httpx
        except ImportError:
            return ChatModelResponse(
                content="httpx required",
                provider=self.provider_id,
                model=model,
                finish_reason="dependency_missing",
            )
        base = os.getenv(self._base_env, self._default_base).rstrip("/")
        payload = {
            "model": model,
            "messages": _messages_with_system(request),
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        try:
            with httpx.Client(timeout=120.0) as client:
                r = client.post(
                    f"{base}/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json=payload,
                )
                r.raise_for_status()
                data = r.json()
            choice = (data.get("choices") or [{}])[0]
            content = (choice.get("message") or {}).get("content") or ""
            return ChatModelResponse(
                content=content,
                provider=self.provider_id,
                model=model,
                finish_reason=choice.get("finish_reason") or "stop",
                usage=data.get("usage") or {},
                safety={"court_ready": False, "legal_advice": False, "external_network": True},
            )
        except Exception as e:
            return ChatModelResponse(
                content=f"{self._name} request failed: {e}",
                provider=self.provider_id,
                model=model,
                finish_reason="error",
                safety={"court_ready": False, "external_network": True},
            )


class AnthropicProvider:
    provider_id = "anthropic"

    def metadata(self) -> dict[str, Any]:
        return {
            "id": self.provider_id,
            "name": "Anthropic Claude",
            "configured": bool(os.getenv("ANTHROPIC_API_KEY")),
            "external_network": True,
            "local": False,
            "models": ["claude-3-5-sonnet-latest", "claude-3-opus-latest"],
            "supports_streaming": False,
            "supports_tools": False,
            "default": False,
            "env_var": "ANTHROPIC_API_KEY",
            "family": "anthropic",
        }

    def complete(self, request: ChatModelRequest) -> ChatModelResponse:
        key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        model = request.model if request.model and "claude" in request.model else "claude-3-5-sonnet-latest"
        if not key:
            return ChatModelResponse(
                content="Anthropic not configured. Set ANTHROPIC_API_KEY after privacy review.",
                provider=self.provider_id,
                model=model,
                finish_reason="provider_unconfigured",
            )
        if os.environ.get("ALA_ALLOW_EXTERNAL_LLM", "").strip().lower() not in ("1", "true", "yes"):
            return ChatModelResponse(
                content="Anthropic gated: set ALA_ALLOW_EXTERNAL_LLM=1 after compliance review.",
                provider=self.provider_id,
                model=model,
                finish_reason="external_gated",
            )
        try:
            import httpx
        except ImportError:
            return ChatModelResponse(
                content="httpx required",
                provider=self.provider_id,
                model=model,
                finish_reason="dependency_missing",
            )
        # Convert messages: system separate
        system = request.system_prompt
        msgs = [m for m in request.messages if m.get("role") in ("user", "assistant")]
        payload = {
            "model": model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": msgs,
        }
        if system:
            payload["system"] = system
        try:
            with httpx.Client(timeout=120.0) as client:
                r = client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json=payload,
                )
                r.raise_for_status()
                data = r.json()
            parts = data.get("content") or []
            content = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
            return ChatModelResponse(
                content=content,
                provider=self.provider_id,
                model=model,
                finish_reason=data.get("stop_reason") or "stop",
                usage=data.get("usage") or {},
                safety={"court_ready": False, "external_network": True},
            )
        except Exception as e:
            return ChatModelResponse(
                content=f"Anthropic request failed: {e}",
                provider=self.provider_id,
                model=model,
                finish_reason="error",
            )


class PuterProvider:
    """Browser-first Puter.js AI gateway (500+ models, user-pays, no server keys).

    Live inference runs in the Platform UI via ``puter.ai.chat()``.
    Server ``complete()`` returns a client-side directive only — we do not
    proxy Puter traffic so the User-Pays model and key-free backend stay intact.
    Docs: https://developer.puter.com/ai/
    """

    provider_id = "puter"

    DEFAULT_MODELS = [
        "gpt-5-nano",
        "gpt-4o-mini",
        "claude-sonnet-4-6",
        "gemini-2.5-flash",
        "deepseek-chat",
        "moonshotai/kimi-k2.5",
        "meta-llama/llama-3.1-70b-instruct",
    ]

    def metadata(self) -> dict[str, Any]:
        default_model = os.environ.get("ALA_PUTER_MODEL", "gpt-5-nano").strip() or "gpt-5-nano"
        models = list(self.DEFAULT_MODELS)
        if default_model not in models:
            models.insert(0, default_model)
        return {
            "id": self.provider_id,
            "name": "Puter AI Gateway",
            "configured": True,
            "external_network": True,
            "local": False,
            "client_side": True,
            "user_pays": True,
            "models": models,
            "default_model": default_model,
            "supports_streaming": True,
            "supports_tools": True,
            "default": True,
            "family": "puter",
            "docs": "https://developer.puter.com/ai/",
            "script": "https://js.puter.com/v2/",
            "note": "User-pays browser AI — no server API keys. Platform UI calls puter.ai.chat().",
        }

    def complete(self, request: ChatModelRequest) -> ChatModelResponse:
        model = request.model if request.model and request.model != "safe-orchestrator" else (
            os.environ.get("ALA_PUTER_MODEL", "gpt-5-nano").strip() or "gpt-5-nano"
        )
        content = (
            "**Puter AI is the browser AI base** for this platform "
            "(https://developer.puter.com/ai/).\n\n"
            "Inference runs client-side with Puter.js — **no server API keys**, "
            "users cover their own usage (User-Pays).\n\n"
            f"Requested model: `{model}` · mode=`{request.mode}`.\n\n"
            "Use the Platform UI with provider **Puter AI Gateway**, or call "
            "`puter.ai.chat(messages, { model })` in the browser. "
            "This server endpoint does not proxy Puter (keeps billing and keys off our backend).\n\n"
            "Not legal advice. Outputs are never court-ready without human review."
        )
        return ChatModelResponse(
            content=content,
            provider=self.provider_id,
            model=model,
            finish_reason="client_side",
            usage={"input_messages": len(request.messages), "output_chars": len(content)},
            safety={
                "court_ready": False,
                "legal_advice": False,
                "external_network": True,
                "client_side": True,
                "user_pays": True,
            },
        )


class KimiProvider:
    """Moonshot Kimi — long-context / agentic intelligence.

    Primary path: browser via Puter.js model ``moonshotai/kimi-k2.5`` (user-pays).
    Optional server path: Moonshot OpenAI-compatible API with MOONSHOT_API_KEY
    + ALA_ALLOW_EXTERNAL_LLM=1.
    Docs: https://platform.kimi.ai/ · Puter: https://developer.puter.com/ai/
    """

    provider_id = "kimi"

    DEFAULT_MODELS = [
        "moonshotai/kimi-k2.5",
        "moonshot-v1-128k",
        "moonshot-v1-32k",
        "kimi-latest",
    ]

    def metadata(self) -> dict[str, Any]:
        default_model = (
            os.environ.get("ALA_KIMI_MODEL", "moonshotai/kimi-k2.5").strip()
            or "moonshotai/kimi-k2.5"
        )
        models = list(self.DEFAULT_MODELS)
        if default_model not in models:
            models.insert(0, default_model)
        has_key = bool(os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY"))
        return {
            "id": self.provider_id,
            "name": "Kimi (Moonshot)",
            "configured": True,  # browser Puter path always available
            "external_network": True,
            "local": False,
            "client_side": True,
            "user_pays": True,
            "server_api_configured": has_key,
            "models": models,
            "default_model": default_model,
            "supports_streaming": True,
            "supports_tools": True,
            "default": False,
            "family": "kimi",
            "docs": "https://www.moonshot.ai/",
            "puter_model": "moonshotai/kimi-k2.5",
            "env_var": "MOONSHOT_API_KEY",
            "note": (
                "Long-context Kimi via Puter (user-pays) or Moonshot API. "
                "Ideal for deep analysis of long records and multi-document reasoning."
            ),
        }

    def complete(self, request: ChatModelRequest) -> ChatModelResponse:
        model = request.model if request.model and request.model != "safe-orchestrator" else (
            os.environ.get("ALA_KIMI_MODEL", "moonshotai/kimi-k2.5").strip()
            or "moonshotai/kimi-k2.5"
        )
        key = (os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY") or "").strip()
        allow = os.environ.get("ALA_ALLOW_EXTERNAL_LLM", "").strip().lower() in ("1", "true", "yes")

        if key and allow:
            # OpenAI-compatible Moonshot endpoint
            try:
                import httpx
            except ImportError:
                return ChatModelResponse(
                    content="httpx required for Moonshot Kimi server path",
                    provider=self.provider_id,
                    model=model,
                    finish_reason="dependency_missing",
                )
            base = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1").rstrip("/")
            # Map Puter-style ids to Moonshot API ids when needed
            api_model = model
            if model.startswith("moonshotai/"):
                api_model = model.split("/", 1)[-1]
            payload = {
                "model": api_model if api_model != "kimi-k2.5" else "moonshot-v1-128k",
                "messages": _messages_with_system(request),
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            }
            try:
                with httpx.Client(timeout=120.0) as client:
                    r = client.post(
                        f"{base}/chat/completions",
                        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                        json=payload,
                    )
                    r.raise_for_status()
                    data = r.json()
                choice = (data.get("choices") or [{}])[0]
                content = (choice.get("message") or {}).get("content") or ""
                return ChatModelResponse(
                    content=content,
                    provider=self.provider_id,
                    model=model,
                    finish_reason=choice.get("finish_reason") or "stop",
                    usage=data.get("usage") or {},
                    safety={
                        "court_ready": False,
                        "legal_advice": False,
                        "external_network": True,
                        "kimi": True,
                    },
                )
            except Exception as e:
                return ChatModelResponse(
                    content=f"Kimi/Moonshot API failed: {e}. Prefer browser Puter path.",
                    provider=self.provider_id,
                    model=model,
                    finish_reason="error",
                    safety={"court_ready": False, "external_network": True},
                )

        content = (
            "**Kimi (Moonshot)** is available as a first-class provider.\n\n"
            f"Model: `{model}` · long-context / deep analysis oriented.\n\n"
            "**Browser path (recommended):** Platform UI provider **Kimi** uses "
            f"`puter.ai.chat(..., {{ model: '{model}' }})` — user-pays, no server keys "
            "(https://developer.puter.com/ai/).\n\n"
            "**Server path (optional):** set `MOONSHOT_API_KEY` (or `KIMI_API_KEY`) and "
            "`ALA_ALLOW_EXTERNAL_LLM=1` after privacy review.\n\n"
            "Not legal advice. Outputs never court-ready without human review."
        )
        return ChatModelResponse(
            content=content,
            provider=self.provider_id,
            model=model,
            finish_reason="client_side",
            usage={"input_messages": len(request.messages)},
            safety={
                "court_ready": False,
                "legal_advice": False,
                "client_side": True,
                "user_pays": True,
                "kimi": True,
            },
        )


class ModelProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, ModelProvider] = {
            "puter": PuterProvider(),
            "kimi": KimiProvider(),
            "safe_local": SafeLocalProvider(),
            "ollama": OllamaProvider(),
            "openai": OpenAICompatibleProvider(),
            "openrouter": OpenAICompatibleProvider(
                provider_id="openrouter",
                name="OpenRouter",
                env_key="OPENROUTER_API_KEY",
                base_env="OPENROUTER_BASE_URL",
                default_base="https://openrouter.ai/api/v1",
                models=[
                    "openai/gpt-4o-mini",
                    "anthropic/claude-3.5-sonnet",
                    "moonshotai/kimi-k2.5",
                    "meta-llama/llama-3.1-70b-instruct",
                ],
            ),
            "anthropic": AnthropicProvider(),
        }

    def list_providers(self) -> list[dict[str, Any]]:
        default_id = self.default_provider_id()
        out: list[dict[str, Any]] = []
        for provider in self._providers.values():
            meta = dict(provider.metadata())
            meta["default"] = meta.get("id") == default_id
            out.append(meta)
        return out

    def get(self, provider_id: str = "puter") -> ModelProvider:
        return self._providers.get(provider_id) or self._providers["puter"]

    def default_provider_id(self) -> str:
        configured = os.getenv("ALA_MODEL_PROVIDER", "puter").strip() or "puter"
        return configured if configured in self._providers else "puter"

    def complete(
        self,
        request: ChatModelRequest,
        *,
        provider_id: str = "",
    ) -> ChatModelResponse:
        pid = provider_id or self.default_provider_id()
        # private_local mode prefers ollama
        if request.mode == "private_local" and not provider_id:
            pid = "ollama"
        return self.get(pid).complete(request)


_registry: ModelProviderRegistry | None = None


def get_model_provider_registry() -> ModelProviderRegistry:
    global _registry
    if _registry is None:
        _registry = ModelProviderRegistry()
    return _registry


def reset_model_provider_registry() -> None:
    global _registry
    _registry = None
