"""Shared pytest fixtures.

Rate limiting is process-global (in-memory). Disable it for normal tests so
parallel/sequential auth fixtures do not trip 429; rate-limit tests re-enable.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _default_disable_rate_limits(monkeypatch, request):
    """Disable auth rate limits unless the test module opts in."""
    # Rate-limit suite re-enables and pins tight rules itself.
    if "test_rate_limit" in request.node.nodeid:
        yield
        return
    monkeypatch.setenv("ALA_RATE_LIMIT_DISABLED", "1")
    try:
        from backend.api.rate_limit import reset_rate_limiter

        reset_rate_limiter()
    except Exception:
        pass
    yield
