"""Deployment readiness gate tests."""

from __future__ import annotations

from scripts import validate_deployment_readiness as gate


def test_deployment_fast_checks_pass():
    results = gate.run_checks(include_slow=False)
    assert results
    assert all(result.ok for result in results), [result for result in results if not result.ok]


def test_public_environment_check_passes_with_safe_defaults(monkeypatch):
    monkeypatch.setenv("APP_MODE", "public_demo")
    monkeypatch.delenv("ALLOW_PUBLIC_UPLOADS", raising=False)
    monkeypatch.delenv("ALLOW_CLIENT_DATA", raising=False)
    monkeypatch.delenv("ALLOW_COURT_READY_EXPORTS", raising=False)
    monkeypatch.delenv("ALLOW_PUBLIC_PERSISTENCE", raising=False)
    monkeypatch.delenv("ALLOW_PUBLIC_CONNECTORS", raising=False)
    result = gate.check_public_environment()
    assert result.ok, result.detail
    assert "'safe': True" in result.detail
