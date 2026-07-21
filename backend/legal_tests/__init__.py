"""Legal test registry and evaluation."""

from architecture.legal_test import (
    LegalTest,
    default_legal_tests,
    retaliatory_eviction_s56_test,
    rta_s56_retaliatory_eviction_test,
)
from backend.legal_tests.evaluate import evaluate_legal_test

__all__ = [
    "LegalTest",
    "default_legal_tests",
    "evaluate_legal_test",
    "retaliatory_eviction_s56_test",
    "rta_s56_retaliatory_eviction_test",
]
