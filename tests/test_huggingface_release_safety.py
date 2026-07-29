"""Regression tests for public Hugging Face release safety."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate-huggingface-assets.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_huggingface_assets", VALIDATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_huggingface_release_assets_pass_safety_gate():
    validator = load_validator()
    assert validator.run_checks() == []


def test_space_uses_standard_pinned_model_loading_only():
    app = (ROOT / "huggingface-space" / "app.py").read_text(encoding="utf-8")
    assert "TRUST_REMOTE_CODE = False" in app
    assert "trust_remote_code=True" not in app
    assert 'MODEL_REVISION = os.environ.get("HF_MODEL_REVISION"' in app
    assert 'BLOCKED_MODEL_TYPES = {"bc_legal_ai_policy_card"}' in app
    assert "AutoConfig.from_pretrained" in app
    assert 'if getattr(config, "auto_map", None)' in app


def test_space_metadata_matches_pinned_runtime():
    readme = (ROOT / "huggingface-space" / "README.md").read_text(encoding="utf-8")
    requirements = (ROOT / "huggingface-space" / "requirements.txt").read_text(
        encoding="utf-8"
    )
    assert "sdk: gradio" in readme
    assert "sdk_version: 5.49.1" in readme
    assert "app_file: app.py" in readme
    assert "gradio==5.49.1" in requirements


def test_publisher_runs_validator_before_authentication():
    publisher = (ROOT / "scripts" / "publish-huggingface.ps1").read_text(encoding="utf-8")
    validation_index = publisher.index("validate-huggingface-assets.py")
    auth_index = publisher.index("auth login")
    assert validation_index < auth_index
