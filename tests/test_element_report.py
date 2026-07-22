"""Element report — disabled s.56 path no longer evaluates."""

from __future__ import annotations

import pytest

from architecture.legal_test import LegalTestDisabledError, rta_s56_retaliatory_eviction_test
from backend.legal_tests.evaluate import evaluate_legal_test


def test_disabled_s56_cannot_produce_element_report():
    with pytest.raises(LegalTestDisabledError):
        evaluate_legal_test(rta_s56_retaliatory_eviction_test(), [])
