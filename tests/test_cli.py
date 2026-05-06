"""Tests for Aegis AI CLI commands using typer.testing.CliRunner."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from aegis.cli.app import app

runner = CliRunner()


def test_app_no_args() -> None:
    """Running without args should show help."""
    result = runner.invoke(app, [])
    assert (
        result.exit_code == 0
        or "--help" in result.output.lower()
        or "usage" in result.output.lower()
    )


def test_help_flag() -> None:
    """--help should return usage info."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "aegis" in result.output.lower() or "Usage" in result.output


def test_run_help() -> None:
    """aegis run --help should show run command options."""
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "--mode" in result.output or "mode" in result.output


def test_mock_target_help() -> None:
    """aegis mock-target --help should show port and mode options."""
    result = runner.invoke(app, ["mock-target", "--help"])
    assert result.exit_code == 0
    assert "--port" in result.output or "port" in result.output


def test_report_help() -> None:
    """aegis report --help should show session and format options."""
    result = runner.invoke(app, ["report", "--help"])
    assert result.exit_code == 0
    assert "--session" in result.output or "session" in result.output


def test_replay_help() -> None:
    """aegis replay --help should work."""
    result = runner.invoke(app, ["replay", "--help"])
    assert result.exit_code == 0


def test_list_sessions_help() -> None:
    """aegis list-sessions --help should work."""
    result = runner.invoke(app, ["list-sessions", "--help"])
    assert result.exit_code == 0


def test_validate_config_missing_file(tmp_path: Path) -> None:
    """validate-config with non-existent file should exit with error."""
    result = runner.invoke(app, ["validate-config", "--config", str(tmp_path / "nonexistent.json")])
    assert result.exit_code != 0


def test_validate_config_valid_file(tmp_path: Path) -> None:
    """validate-config with a valid config file should succeed."""
    config = {
        "endpoint": "http://localhost:9000/chat",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "api_key": "test-key-12345",
        "timeout": 30,
        "concurrency": 5,
        "mode": "standard",
        "system_prompt": "You are a test assistant.",
    }
    config_path = tmp_path / "target.json"
    config_path.write_text(json.dumps(config))

    result = runner.invoke(app, ["validate-config", "--config", str(config_path)])
    assert result.exit_code == 0
    assert "valid" in result.output.lower() or "endpoint" in result.output.lower()


def test_validate_config_invalid_mode(tmp_path: Path) -> None:
    """validate-config with invalid mode should fail."""
    config = {
        "endpoint": "http://localhost:9000/chat",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "api_key": "",
        "mode": "ultrafast",  # invalid
    }
    config_path = tmp_path / "bad_config.json"
    config_path.write_text(json.dumps(config))

    result = runner.invoke(app, ["validate-config", "--config", str(config_path)])
    assert result.exit_code != 0


def test_report_missing_session(tmp_path: Path) -> None:
    """aegis report with non-existent session should exit with error."""
    result = runner.invoke(app, ["report", "--session", "nonexistent-session-id"])
    assert result.exit_code != 0


def test_replay_missing_session() -> None:
    """aegis replay with non-existent session should exit with error."""
    result = runner.invoke(app, ["replay", "--session", "nonexistent-session-999"])
    assert result.exit_code != 0
