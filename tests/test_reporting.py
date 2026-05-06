"""Tests for Aegis AI report building and export."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aegis.config.target_config import TargetConfig
from aegis.core.context_manager import ContextManager
from aegis.core.session import Session
from aegis.reporting.export import export_json, export_markdown, export_txt
from aegis.reporting.report_builder import ReportBuilder, _scrub_secrets
from tests.mocks.mock_responses import (
    ALL_FAIL_RESULTS,
    ALL_PASS_RESULTS,
    ALL_RESULTS,
    VALIDATION_FAIL_OVERRIDE,
    VALIDATION_FAIL_SYSTEM_PROMPT,
    VALIDATION_PASS,
    VALIDATION_WARNING,
)


@pytest.fixture
def target_config() -> TargetConfig:
    return TargetConfig(
        endpoint="http://localhost:9000/chat",
        provider="openai",
        model="gpt-4o-mini",
        api_key="sk-secret-test-key-abcd1234",
    )


@pytest.fixture
async def populated_context() -> ContextManager:
    context = ContextManager()
    from aegis.core.models import ReconFindings

    await context.set_recon_findings(
        ReconFindings(
            guardrail_strength="weak",
            refusal_style="polite",
            susceptible_vectors=["jailbreak", "data_exfiltration"],
        )
    )
    for result in ALL_RESULTS:
        await context.add_attack_result(result)
    for vr in [VALIDATION_PASS, VALIDATION_FAIL_SYSTEM_PROMPT, VALIDATION_FAIL_OVERRIDE, VALIDATION_WARNING]:
        await context.add_validation_result(vr)
    return context


@pytest.fixture
def session() -> Session:
    s = Session()
    s.start()
    s.finish("completed")
    return s


@pytest.fixture
async def report_data(
    populated_context: ContextManager,
    session: Session,
    target_config: TargetConfig,
) -> dict:
    builder = ReportBuilder(
        session=session,
        context=populated_context,
        target_config=target_config,
        risk_score=65.5,
    )
    return builder.build()


def test_report_has_required_sections(report_data: dict) -> None:
    """Report should contain all required top-level sections."""
    required_keys = [
        "meta",
        "target",
        "executive_summary",
        "risk",
        "statistics",
        "findings",
        "token_usage",
        "estimated_cost",
        "recommendations",
    ]
    for key in required_keys:
        assert key in report_data, f"Missing key: {key}"


def test_report_scrubs_api_key(report_data: dict) -> None:
    """API key should not appear anywhere in the report."""
    report_str = json.dumps(report_data)
    assert "sk-secret-test-key-abcd1234" not in report_str
    assert "[REDACTED]" in report_str or "REDACTED" in report_str


def test_report_risk_score(report_data: dict) -> None:
    """Risk score should be present and correct."""
    assert report_data["risk"]["score"] == 65.5
    assert report_data["risk"]["level"] in ("Critical", "High", "Medium", "Low")


def test_report_target_endpoint(report_data: dict) -> None:
    """Target endpoint should be in report."""
    assert report_data["target"]["endpoint"] == "http://localhost:9000/chat"


def test_report_has_findings(report_data: dict) -> None:
    """Report should contain findings."""
    assert isinstance(report_data["findings"], list)


def test_report_recommendations_present(report_data: dict) -> None:
    """Report should contain recommendations."""
    assert isinstance(report_data["recommendations"], list)
    assert len(report_data["recommendations"]) > 0


def test_scrub_secrets_function() -> None:
    """_scrub_secrets should redact API keys."""
    text = "Authorization: Bearer sk-1234567890abcdefghijklmnop"
    scrubbed = _scrub_secrets(text)
    assert "sk-1234567890abcdef" not in scrubbed
    assert "[REDACTED]" in scrubbed


def test_scrub_secrets_no_false_positives() -> None:
    """_scrub_secrets should not alter regular text."""
    text = "The risk score is High. Recommendations follow."
    assert _scrub_secrets(text) == text


def test_export_json(tmp_path: Path, report_data: dict) -> None:
    """export_json should write valid JSON to disk."""
    output_path = tmp_path / "report.json"
    export_json(report_data, output_path)

    assert output_path.exists()
    loaded = json.loads(output_path.read_text())
    assert loaded["meta"]["tool"] == "Aegis AI"


def test_export_txt(tmp_path: Path, report_data: dict) -> None:
    """export_txt should write readable text report."""
    output_path = tmp_path / "report.txt"
    export_txt(report_data, output_path)

    assert output_path.exists()
    content = output_path.read_text()
    assert "AEGIS AI RED-TEAM REPORT" in content
    assert "RISK ASSESSMENT" in content
    assert "FINDINGS" in content


def test_export_markdown(tmp_path: Path, report_data: dict) -> None:
    """export_markdown should write a markdown file."""
    output_path = tmp_path / "report.md"
    export_markdown(report_data, output_path)

    assert output_path.exists()
    content = output_path.read_text()
    assert "Aegis AI" in content
    assert "Risk Assessment" in content or "risk" in content.lower()


def test_export_creates_parent_dirs(tmp_path: Path, report_data: dict) -> None:
    """Export functions should create parent directories."""
    deep_path = tmp_path / "reports" / "session-abc" / "report.json"
    export_json(report_data, deep_path)
    assert deep_path.exists()


def test_export_json_no_secrets(tmp_path: Path, report_data: dict) -> None:
    """Exported JSON should not contain raw API keys."""
    output_path = tmp_path / "report.json"
    export_json(report_data, output_path)
    content = output_path.read_text()
    assert "sk-secret-test-key-abcd1234" not in content
