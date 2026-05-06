"""Tests for Aegis AI risk scoring."""

from __future__ import annotations

import pytest

from aegis.core.models import ValidationResult, ValidationStatus
from aegis.reporting.risk_scoring import RiskScoring


@pytest.fixture
def scorer() -> RiskScoring:
    return RiskScoring()


def _make_vr(
    attack_id: str,
    status: ValidationStatus,
    severity: str = "High",
    confidence: float = 0.9,
    owasp: list[str] | None = None,
) -> ValidationResult:
    return ValidationResult(
        attack_id=attack_id,
        result=status,
        confidence=confidence,
        evidence="test",
        owasp_mappings=owasp or ["LLM01"],
        severity=severity,
        validator_name="test",
    )


def test_empty_results_score_zero(scorer: RiskScoring) -> None:
    """No results should give score of 0."""
    assert scorer.calculate([]) == 0.0


def test_all_pass_score_zero(scorer: RiskScoring) -> None:
    """All PASS results should give score of 0."""
    results = [_make_vr(f"t-{i}", ValidationStatus.PASS) for i in range(5)]
    score = scorer.calculate(results)
    assert score == 0.0


def test_all_fail_high_score(scorer: RiskScoring) -> None:
    """All FAIL results with high severity should give high score."""
    results = [
        _make_vr(f"t-{i}", ValidationStatus.FAIL, severity="High", confidence=0.95)
        for i in range(5)
    ]
    score = scorer.calculate(results)
    assert score > 50  # Should be a significant score


def test_mixed_results_intermediate_score(scorer: RiskScoring) -> None:
    """Mix of PASS and FAIL should give intermediate score."""
    results = [
        _make_vr("pass-1", ValidationStatus.PASS),
        _make_vr("pass-2", ValidationStatus.PASS),
        _make_vr("fail-1", ValidationStatus.FAIL),
        _make_vr("warn-1", ValidationStatus.WARNING),
    ]
    score = scorer.calculate(results)
    assert 0 < score < 100


def test_score_bounded_0_100(scorer: RiskScoring) -> None:
    """Score should always be between 0 and 100."""
    results = [
        _make_vr(f"extreme-{i}", ValidationStatus.FAIL, severity="Critical", confidence=1.0)
        for i in range(20)
    ]
    score = scorer.calculate(results)
    assert 0.0 <= score <= 100.0


def test_get_level_critical(scorer: RiskScoring) -> None:
    """Score >= 90 should be Critical."""
    assert scorer.get_level(95.0) == "Critical"
    assert scorer.get_level(90.0) == "Critical"


def test_get_level_high(scorer: RiskScoring) -> None:
    """Score 71-89 should be High."""
    assert scorer.get_level(80.0) == "High"
    assert scorer.get_level(71.0) == "High"


def test_get_level_medium(scorer: RiskScoring) -> None:
    """Score 31-70 should be Medium."""
    assert scorer.get_level(50.0) == "Medium"
    assert scorer.get_level(31.0) == "Medium"


def test_get_level_low(scorer: RiskScoring) -> None:
    """Score 0-30 should be Low."""
    assert scorer.get_level(0.0) == "Low"
    assert scorer.get_level(25.0) == "Low"


def test_severity_affects_score(scorer: RiskScoring) -> None:
    """Higher severity failures should produce higher scores."""
    low_sev = [_make_vr("low-1", ValidationStatus.FAIL, severity="Low")]
    high_sev = [_make_vr("high-1", ValidationStatus.FAIL, severity="Critical")]

    low_score = scorer.calculate(low_sev)
    high_score = scorer.calculate(high_sev)
    assert high_score > low_score


def test_confidence_affects_score(scorer: RiskScoring) -> None:
    """Higher confidence failures should produce higher scores."""
    low_conf = [_make_vr("lc-1", ValidationStatus.FAIL, confidence=0.3)]
    high_conf = [_make_vr("hc-1", ValidationStatus.FAIL, confidence=0.95)]

    low_score = scorer.calculate(low_conf)
    high_score = scorer.calculate(high_conf)
    assert high_score > low_score


def test_warnings_produce_lower_score_than_fails(scorer: RiskScoring) -> None:
    """WARNING results should score lower than FAIL results."""
    fail_results = [_make_vr("f1", ValidationStatus.FAIL, confidence=0.9)]
    warn_results = [_make_vr("w1", ValidationStatus.WARNING, confidence=0.9)]

    assert scorer.calculate(fail_results) > scorer.calculate(warn_results)
