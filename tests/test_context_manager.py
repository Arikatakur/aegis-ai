"""Tests for Aegis AI ContextManager (blackboard pattern)."""

from __future__ import annotations

import asyncio
from datetime import datetime

import pytest

from aegis.core.context_manager import ContextManager
from aegis.core.models import (
    AttackResult,
    ReconFindings,
    ValidationResult,
    ValidationStatus,
)


@pytest.fixture
def context() -> ContextManager:
    return ContextManager()


@pytest.fixture
def sample_attack_result() -> AttackResult:
    return AttackResult(
        attack_id="test-001",
        agent_name="jailbreak",
        category="jailbreak",
        prompt="Test prompt",
        response="Test response",
        status_code=200,
        latency_ms=150.0,
        prompt_tokens=10,
        completion_tokens=20,
        estimated_cost=0.0001,
        timestamp=datetime.utcnow(),
    )


@pytest.fixture
def sample_validation_result(sample_attack_result: AttackResult) -> ValidationResult:
    return ValidationResult(
        attack_id=sample_attack_result.attack_id,
        result=ValidationStatus.PASS,
        confidence=0.9,
        evidence="No issues found.",
        owasp_mappings=["LLM01"],
        severity="High",
        validator_name="rule_validator",
    )


@pytest.fixture
def sample_recon() -> ReconFindings:
    return ReconFindings(
        guardrail_strength="moderate",
        refusal_style="polite",
        suspected_filters=["harm_filter"],
        susceptible_vectors=["jailbreak", "prompt_injection"],
        recommended_agents=["JailbreakAgent", "PromptInjectionAgent"],
    )


async def test_initial_state(context: ContextManager) -> None:
    """Context should start empty."""
    assert context.recon_findings is None
    assert context.attack_results == []
    assert context.validation_results == []
    assert context.token_usage["total_tokens"] == 0


async def test_set_recon_findings(context: ContextManager, sample_recon: ReconFindings) -> None:
    """Setting recon findings should update context and selected vectors."""
    await context.set_recon_findings(sample_recon)
    assert context.recon_findings is not None
    assert context.recon_findings.guardrail_strength == "moderate"
    assert "jailbreak" in context.selected_vectors


async def test_add_attack_result(
    context: ContextManager, sample_attack_result: AttackResult
) -> None:
    """Adding attack results should update token counts."""
    await context.add_attack_result(sample_attack_result)
    assert len(context.attack_results) == 1
    assert context.token_usage["prompt_tokens"] == 10
    assert context.token_usage["completion_tokens"] == 20
    assert context.token_usage["total_tokens"] == 30


async def test_add_multiple_attack_results(context: ContextManager) -> None:
    """Adding multiple results should accumulate token counts."""
    for i in range(3):
        result = AttackResult(
            attack_id=f"test-{i:03d}",
            agent_name="jailbreak",
            category="jailbreak",
            prompt="test",
            response="response",
            prompt_tokens=5,
            completion_tokens=10,
        )
        await context.add_attack_result(result)

    assert len(context.attack_results) == 3
    assert context.token_usage["total_tokens"] == 45


async def test_add_validation_result_pass(
    context: ContextManager,
    sample_attack_result: AttackResult,
    sample_validation_result: ValidationResult,
) -> None:
    """PASS validation should add to successful_patterns."""
    await context.add_attack_result(sample_attack_result)
    await context.add_validation_result(sample_validation_result)
    assert len(context.validation_results) == 1
    assert len(context.successful_patterns) == 1


async def test_add_validation_result_fail(context: ContextManager) -> None:
    """FAIL validation should add to failed_patterns."""
    result = AttackResult(
        attack_id="fail-001",
        agent_name="jailbreak",
        category="jailbreak",
        prompt="A jailbreak prompt",
        response="AEGIS_PROBE_OK",
    )
    vr = ValidationResult(
        attack_id="fail-001",
        result=ValidationStatus.FAIL,
        confidence=0.95,
        evidence="Pattern found.",
        owasp_mappings=["LLM01"],
        severity="jailbreak",
        validator_name="rule_validator",
    )
    await context.add_attack_result(result)
    await context.add_validation_result(vr)
    assert len(context.failed_patterns) == 1


async def test_get_summary(
    context: ContextManager,
    sample_attack_result: AttackResult,
    sample_validation_result: ValidationResult,
    sample_recon: ReconFindings,
) -> None:
    """get_summary should return correct counts."""
    await context.set_recon_findings(sample_recon)
    await context.add_attack_result(sample_attack_result)
    await context.add_validation_result(sample_validation_result)

    summary = context.get_summary()
    assert summary["total_attacks"] == 1
    assert summary["passed"] == 1
    assert summary["failed"] == 0
    assert summary["warnings"] == 0
    assert summary["guardrail_strength"] == "moderate"


async def test_to_dict(context: ContextManager, sample_recon: ReconFindings) -> None:
    """to_dict should produce a serialisable dict."""
    await context.set_recon_findings(sample_recon)
    data = context.to_dict()
    assert "recon_findings" in data
    assert data["recon_findings"]["guardrail_strength"] == "moderate"
    assert "attack_results" in data
    assert "validation_results" in data


async def test_concurrent_access(context: ContextManager) -> None:
    """Multiple coroutines adding results concurrently should not corrupt state."""

    async def add_results(start_idx: int) -> None:
        for i in range(5):
            result = AttackResult(
                attack_id=f"concurrent-{start_idx}-{i}",
                agent_name="test",
                category="test",
                prompt="p",
                response="r",
                prompt_tokens=1,
                completion_tokens=1,
            )
            await context.add_attack_result(result)

    await asyncio.gather(add_results(0), add_results(1), add_results(2))
    assert len(context.attack_results) == 15
    assert context.token_usage["total_tokens"] == 30
