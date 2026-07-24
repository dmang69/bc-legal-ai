"""Model provider abstraction for conversational platform.

Production providers must be configured explicitly. The default provider is a
safe deterministic local orchestrator so tests and development never silently
send confidential data to an external model.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Protocol


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


class SafeLocalProvider:
    provider_id = "safe_local"

    def metadata(self) -> dict[str, Any]:
        return {
            "id": self.provider_id,
            "name": "Safe Local Orchestrator",
            "configured": True,
            "external_network": False,
            "models": ["safe-orchestrator"],
            "supports_streaming": True,
            "supports_tools": True,
            "default": True,
        }

    def complete(self, request: ChatModelRequest) -> ChatModelResponse:
        last = next((m.get("content", "") for m in reversed(request.messages) if m.get("role") == "user"), "")
        content = (
            "I can help with that in a supervised workspace. "
            "I will keep legal outputs non-court-ready until citations, evidence, privilege, "
            "and human approval gates are complete.\n\n"
            f"Request: {last[:1200]}"
        )
        return ChatModelResponse(
            content=content,
            provider=self.provider_id,
            model=request.model or "safe-orchestrator",
            usage={"input_messages": len(request.messages), "output_chars": len(content)},
            safety={"court_ready": False, "legal_advice": False, "external_network": False},
        )


class UnconfiguredExternalProvider:
    def __init__(self, provider_id: str, name: str, env_var: str, models: list[str]) -> None:
        self.provider_id = provider_id
        self._name = name
        self._env_var = env_var
        self._models = models

    def metadata(self) -> dict[str, Any]:
        return {
            "id": self.provider_id,
            "name": self._name,
            "configured": bool(os.getenv(self._env_var)),
            "external_network": True,
            "models": self._models,
            "supports_streaming": False,
            "supports_tools": False,
            "default": False,
            "env_var": self._env_var,
        }

    def complete(self, request: ChatModelRequest) -> ChatModelResponse:
        if not os.getenv(self._env_var):
            return ChatModelResponse(
                content=(
                    f"Provider {self._name} is not configured. "
                    f"Set {self._env_var} and complete privacy/security review before use."
                ),
                provider=self.provider_id,
                model=request.model,
                finish_reason="provider_unconfigured",
                safety={"court_ready": False, "legal_advice": False, "external_network": True},
            )
        return ChatModelResponse(
            content=(
                f"Provider {self._name} is configured but live external inference is disabled "
                "in this build until an approved gateway implementation is added."
            ),
            provider=self.provider_id,
            model=request.model,
            finish_reason="gateway_not_implemented",
            safety={"court_ready": False, "legal_advice": False, "external_network": True},
        )


class ModelProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, ModelProvider] = {
            "safe_local": SafeLocalProvider(),
            "openai": UnconfiguredExternalProvider("openai", "OpenAI-compatible", "OPENAI_API_KEY", ["gpt-4.1", "gpt-4o", "o3"]),
            "anthropic": UnconfiguredExternalProvider("anthropic", "Anthropic Claude", "ANTHROPIC_API_KEY", ["claude-3-5-sonnet", "claude-3-opus"]),
            "openrouter": UnconfiguredExternalProvider("openrouter", "OpenRouter", "OPENROUTER_API_KEY", ["kimi", "qwen", "llama", "mistral"]),
            "local_llm": UnconfiguredExternalProvider("local_llm", "Local LLM Gateway", "LOCAL_LLM_URL", ["qwen-local", "llama-local"]),
        }

    def list_providers(self) -> list[dict[str, Any]]:
        return [provider.metadata() for provider in self._providers.values()]

    def get(self, provider_id: str = "safe_local") -> ModelProvider:
        return self._providers.get(provider_id) or self._providers["safe_local"]

    def default_provider_id(self) -> str:
        configured = os.getenv("ALA_MODEL_PROVIDER", "safe_local").strip() or "safe_local"
        return configured if configured in self._providers else "safe_local"


_registry: ModelProviderRegistry | None = None


def get_model_provider_registry() -> ModelProviderRegistry:
    global _registry
    if _registry is None:
        _registry = ModelProviderRegistry()
    return _registry
