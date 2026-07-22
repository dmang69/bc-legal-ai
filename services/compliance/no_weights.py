"""
No-weights inference guardrails for public demos and statute paths.

Public Space: CPU-only, no model weights, no statute from memory.
Private workbench: RAG-first; LoRA second (see model/BASE_MODEL_DECISION.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class WeightsPolicy(str, Enum):
    PUBLIC_DEMO = "PUBLIC_DEMO"  # no weights, no inference
    PRIVATE_RAG = "PRIVATE_RAG"  # retrieval + optional LoRA
    BLOCKED = "BLOCKED"


@dataclass
class NoWeightsGuard:
    mode: WeightsPolicy = WeightsPolicy.PUBLIC_DEMO

    def may_load_weights(self) -> bool:
        return self.mode == WeightsPolicy.PRIVATE_RAG

    def may_run_inference(self) -> bool:
        return self.mode == WeightsPolicy.PRIVATE_RAG

    def may_quote_statute_from_model(self) -> bool:
        return False  # never

    def check_request(self, *, wants_inference: bool, wants_statute_from_model: bool) -> tuple[bool, str]:
        if wants_statute_from_model:
            return False, "Refuse: statute text from model weights is forbidden."
        if wants_inference and not self.may_run_inference():
            return False, f"Refuse: inference disabled in mode {self.mode.value}."
        return True, "ok"
