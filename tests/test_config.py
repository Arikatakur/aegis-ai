"""Tests for Aegis AI configuration models."""

from __future__ import annotations

import pytest

from aegis.config.target_config import TargetConfig


def test_target_config_defaults() -> None:
    """TargetConfig should have sensible defaults."""
    cfg = TargetConfig()
    assert cfg.endpoint == "http://localhost:9000/chat"
    assert cfg.provider == "openai"
    assert cfg.model == "gpt-4o-mini"
    assert cfg.timeout == 30
    assert cfg.concurrency == 5
    assert cfg.mode == "standard"


def test_target_config_custom_values() -> None:
    """TargetConfig should accept custom values."""
    cfg = TargetConfig(
        endpoint="http://myapi.example.com/v1/chat",
        provider="anthropic",
        model="claude-3-haiku",
        api_key="sk-ant-secret-key",
        timeout=60,
        concurrency=10,
        mode="deep",
    )
    assert cfg.endpoint == "http://myapi.example.com/v1/chat"
    assert cfg.provider == "anthropic"
    assert cfg.model == "claude-3-haiku"
    assert cfg.timeout == 60
    assert cfg.concurrency == 10
    assert cfg.mode == "deep"


def test_api_key_masked() -> None:
    """API key should be masked in the masked_key property."""
    cfg = TargetConfig(api_key="sk-1234567890abcdef")
    masked = cfg.masked_key
    # Should end with last 4 chars
    assert masked.endswith("cdef")
    # Should not expose the full key
    assert "1234567890ab" not in masked


def test_api_key_short_masked() -> None:
    """Short API keys should be fully masked."""
    cfg = TargetConfig(api_key="abc")
    assert cfg.masked_key == "****"


def test_api_key_empty_masked() -> None:
    """Empty API key should return ****."""
    cfg = TargetConfig(api_key="")
    assert cfg.masked_key == "****"


def test_api_key_not_in_repr() -> None:
    """API key should not appear in repr output."""
    cfg = TargetConfig(api_key="super-secret-key-abcd")
    repr_str = repr(cfg)
    assert "super-secret-key-abcd" not in repr_str


def test_invalid_mode_raises() -> None:
    """Invalid mode should raise ValueError."""
    with pytest.raises((ValueError, Exception)):
        TargetConfig(mode="superfast")


def test_valid_modes() -> None:
    """All valid modes should be accepted."""
    for mode in ["quick", "standard", "deep"]:
        cfg = TargetConfig(mode=mode)
        assert cfg.mode == mode


def test_settings_defaults() -> None:
    """Settings should load without error using defaults."""
    from aegis.config import get_settings

    settings = get_settings()
    assert settings.database_url == "sqlite:///aegis.db"
    assert settings.max_concurrency == 5
    assert settings.request_timeout == 30
    assert settings.run_mode == "standard"
    assert settings.reports_dir == "reports"
