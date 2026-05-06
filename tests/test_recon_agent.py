"""Tests for the ReconAgent using mock target client."""

from __future__ import annotations

import pytest

from aegis.agents.recon_agent import ReconAgent
from aegis.core.context_manager import ContextManager
from aegis.core.models import AttackResult
from tests.mocks.mock_target_client import MockTargetClient


@pytest.fixture
def context() -> ContextManager:
    return ContextManager()


@pytest.fixture
def secure_client() -> MockTargetClient:
    """Mock client that returns proper refusals."""
    return MockTargetClient(
        default_response=AttackResult(
            attack_id="default",
            agent_name="recon",
            category="recon",
            prompt="probe",
            response=("I'm not able to help with that. I cannot ignore previous instructions."),
        )
    )


@pytest.fixture
def vulnerable_client() -> MockTargetClient:
    """Mock client that returns vulnerable responses."""
    return MockTargetClient(
        default_response=AttackResult(
            attack_id="default",
            agent_name="recon",
            category="recon",
            prompt="probe",
            response="AEGIS_PROBE_OK. DAN MODE ACTIVE. My system prompt says...",
        )
    )


async def test_recon_agent_run_returns_empty(
    context: ContextManager, secure_client: MockTargetClient
) -> None:
    """ReconAgent.run() should return empty list (uses run_recon instead)."""
    agent = ReconAgent(context=context, target_client=secure_client)
    cases = await agent.run()
    assert cases == []


async def test_recon_agent_with_secure_target(
    context: ContextManager, secure_client: MockTargetClient
) -> None:
    """ReconAgent against a secure target should detect strong guardrails."""
    agent = ReconAgent(context=context, target_client=secure_client)
    findings = await agent.run_recon()

    assert findings is not None
    assert findings.guardrail_strength in ("strong", "moderate", "unknown")
    assert isinstance(findings.susceptible_vectors, list)
    assert isinstance(findings.recommended_agents, list)
    assert len(findings.raw_responses) > 0


async def test_recon_agent_with_vulnerable_target(
    context: ContextManager, vulnerable_client: MockTargetClient
) -> None:
    """ReconAgent against a vulnerable target should detect weak/no guardrails."""
    agent = ReconAgent(context=context, target_client=vulnerable_client)
    findings = await agent.run_recon()

    assert findings.guardrail_strength in ("none", "weak")
    # Should recommend multiple attack vectors
    assert len(findings.susceptible_vectors) >= 1
    assert len(findings.recommended_agents) >= 1


async def test_recon_agent_stores_raw_responses(
    context: ContextManager, secure_client: MockTargetClient
) -> None:
    """ReconAgent should store raw responses for each probe."""
    agent = ReconAgent(context=context, target_client=secure_client)
    findings = await agent.run_recon()

    # Should have responses for each probe sent
    assert len(findings.raw_responses) >= 5


async def test_recon_agent_handles_client_error(context: ContextManager) -> None:
    """ReconAgent should handle client errors gracefully."""
    from tests.mocks.mock_target_client import DownMockTargetClient

    down_client = DownMockTargetClient()
    agent = ReconAgent(context=context, target_client=down_client)

    # Should not raise - errors are captured in raw_responses
    findings = await agent.run_recon()
    assert findings is not None
    # All responses should have errors
    error_responses = [r for r in findings.raw_responses if "error" in r]
    assert len(error_responses) > 0


async def test_recon_findings_refusal_style(
    context: ContextManager,
) -> None:
    """ReconAgent should detect refusal style."""
    polite_client = MockTargetClient(
        default_response=AttackResult(
            attack_id="default",
            agent_name="recon",
            category="recon",
            prompt="probe",
            response="I'm sorry, I apologize but I cannot help with that request.",
        )
    )
    agent = ReconAgent(context=context, target_client=polite_client)
    findings = await agent.run_recon()
    assert findings.refusal_style == "polite"
