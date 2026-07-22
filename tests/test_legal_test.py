"""LegalTest — disabled s.56 retaliation mapping (P0)."""

from __future__ import annotations

import pytest

from architecture.legal_test import (
    LegalTestDisabledError,
    default_callable_legal_tests,
    rta_s56_retaliatory_eviction_test,
)
from backend.legal_tests.evaluate import evaluate_legal_test


def test_s56_retaliation_test_is_disabled():
    t = rta_s56_retaliatory_eviction_test()
    assert t.test_id == "RTA-s56-retaliatory-eviction"
    assert t.disabled is True
    assert t.authority_status == "DISABLED"
    assert "NOT" in t.disabled_reason.upper() or "incorrect" in t.disabled_reason.lower()
    assert t.elements == []


def test_disabled_test_refuses_evaluation():
    t = rta_s56_retaliatory_eviction_test()
    with pytest.raises(LegalTestDisabledError):
        evaluate_legal_test(t, [])


def test_disabled_not_in_callable_registry():
    assert default_callable_legal_tests() == {}


def test_to_dict_includes_disabled_flag():
    d = rta_s56_retaliatory_eviction_test().to_dict()
    assert d["disabled"] is True
    assert d["authority_status"] == "DISABLED"
