"""Tests for attack agent template loading and AttackCase generation."""

from __future__ import annotations

import pytest

from aegis.agents.context_poisoning_agent import ContextPoisoningAgent
from aegis.agents.data_exfiltration_agent import DataExfiltrationAgent
from aegis.agents.encoding_agent import EncodingAgent
from aegis.agents.jailbreak_agent import JailbreakAgent
from aegis.agents.prompt_injection_agent import PromptInjectionAgent
from aegis.core.context_manager import ContextManager
from aegis.core.exceptions import TemplateLoadError
from aegis.core.models import AttackCase


@pytest.fixture
def context() -> ContextManager:
    return ContextManager()


async def test_jailbreak_agent_loads_templates(context: ContextManager) -> None:
    """JailbreakAgent should load templates and return AttackCase objects."""
    agent = JailbreakAgent(context=context)
    cases = await agent.run()

    assert len(cases) >= 8
    for case in cases:
        assert isinstance(case, AttackCase)
        assert case.category == "jailbreak"
        assert case.agent_name == "jailbreak"
        assert len(case.prompt) > 10
        assert "LLM01" in case.owasp_mappings


async def test_prompt_injection_agent_loads_templates(context: ContextManager) -> None:
    """PromptInjectionAgent should load templates and return AttackCase objects."""
    agent = PromptInjectionAgent(context=context)
    cases = await agent.run()

    assert len(cases) >= 8
    for case in cases:
        assert isinstance(case, AttackCase)
        assert case.category == "prompt_injection"
        assert case.agent_name == "prompt_injection"
        assert len(case.prompt) > 5


async def test_data_exfiltration_agent_loads_templates(context: ContextManager) -> None:
    """DataExfiltrationAgent should load templates and return AttackCase objects."""
    agent = DataExfiltrationAgent(context=context)
    cases = await agent.run()

    assert len(cases) >= 6
    for case in cases:
        assert isinstance(case, AttackCase)
        assert case.category == "data_exfiltration"
        assert case.agent_name == "data_exfiltration"


async def test_encoding_agent_loads_templates(context: ContextManager) -> None:
    """EncodingAgent should load templates and return AttackCase objects."""
    agent = EncodingAgent(context=context)
    cases = await agent.run()

    assert len(cases) >= 5
    for case in cases:
        assert isinstance(case, AttackCase)
        assert case.category == "encoding"
        assert case.agent_name == "encoding"


async def test_context_poisoning_agent_loads_templates(context: ContextManager) -> None:
    """ContextPoisoningAgent should load templates and return AttackCase objects."""
    agent = ContextPoisoningAgent(context=context)
    cases = await agent.run()

    assert len(cases) >= 5
    for case in cases:
        assert isinstance(case, AttackCase)
        assert case.category == "context_poisoning"
        assert case.agent_name == "context_poisoning"


async def test_all_agents_have_unique_attack_ids(context: ContextManager) -> None:
    """All attack IDs across all agents should be unique."""
    agents = [
        JailbreakAgent(context=context),
        PromptInjectionAgent(context=context),
        DataExfiltrationAgent(context=context),
        EncodingAgent(context=context),
        ContextPoisoningAgent(context=context),
    ]
    all_ids: list[str] = []
    for agent in agents:
        cases = await agent.run()
        all_ids.extend(c.attack_id for c in cases)

    # All IDs should be unique
    assert len(all_ids) == len(set(all_ids))


def test_load_templates_invalid_category(context: ContextManager) -> None:
    """load_templates with unknown category should raise TemplateLoadError."""
    agent = JailbreakAgent(context=context)
    with pytest.raises(TemplateLoadError):
        agent.load_templates("nonexistent_category")


async def test_attack_case_has_required_fields(context: ContextManager) -> None:
    """Every AttackCase should have all required fields populated."""
    agent = JailbreakAgent(context=context)
    cases = await agent.run()

    for case in cases:
        assert case.attack_id, "attack_id must not be empty"
        assert case.agent_name, "agent_name must not be empty"
        assert case.category, "category must not be empty"
        assert case.prompt, "prompt must not be empty"
        assert isinstance(case.owasp_mappings, list)
        assert isinstance(case.metadata, dict)


async def test_attack_planner_quick_mode(context: ContextManager) -> None:
    """AttackPlanner in quick mode should return fewer cases."""
    from aegis.agents.attack_planner import AttackPlanner
    from aegis.core.models import ReconFindings

    await context.set_recon_findings(
        ReconFindings(
            guardrail_strength="weak",
            susceptible_vectors=["jailbreak", "prompt_injection"],
            recommended_agents=["JailbreakAgent", "PromptInjectionAgent"],
        )
    )

    planner = AttackPlanner(context=context)
    cases_quick = await planner.plan(mode="quick")
    cases_standard = await planner.plan(mode="standard")

    assert len(cases_quick) <= len(cases_standard)
    # Quick mode limits to 2 per agent
    assert len(cases_quick) <= 4  # 2 agents * 2 cases each


async def test_attack_planner_no_recon(context: ContextManager) -> None:
    """AttackPlanner with no recon findings should still return cases."""
    from aegis.agents.attack_planner import AttackPlanner

    planner = AttackPlanner(context=context)
    cases = await planner.plan(mode="quick")

    assert isinstance(cases, list)
    assert len(cases) > 0
