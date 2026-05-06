"""Attack planner - selects and prioritises attack agents based on recon findings."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from aegis.agents.base_agent import BaseAgent
from aegis.core.models import AttackCase

if TYPE_CHECKING:
    from aegis.core.context_manager import ContextManager

logger = logging.getLogger(__name__)

# Mapping of vector names to agent classes
_VECTOR_TO_AGENT: dict[str, str] = {
    "jailbreak": "JailbreakAgent",
    "prompt_injection": "PromptInjectionAgent",
    "data_exfiltration": "DataExfiltrationAgent",
    "encoding": "EncodingAgent",
    "context_poisoning": "ContextPoisoningAgent",
}

# Mode filters: number of cases to take from each agent
_MODE_LIMITS: dict[str, int] = {
    "quick": 2,
    "standard": 5,
    "deep": 999,  # all
}


class AttackPlanner:
    """Reads recon findings and selects attack cases to execute.

    Applies mode-based filters so quick runs stay fast.
    """

    def __init__(self, context: ContextManager) -> None:
        self.context = context

    async def plan(self, mode: str = "standard") -> list[AttackCase]:
        """Select and return attack cases based on recon findings.

        Args:
            mode: Run mode controlling how many cases per agent.

        Returns:
            Flat list of AttackCase objects for all selected agents.
        """
        findings = self.context.recon_findings
        if findings is None:
            logger.warning("No recon findings available - using all vectors")
            vectors = list(_VECTOR_TO_AGENT.keys())
        else:
            vectors = findings.susceptible_vectors or list(_VECTOR_TO_AGENT.keys())

        limit = _MODE_LIMITS.get(mode, 5)
        all_cases: list[AttackCase] = []

        for vector in vectors:
            agent_class_name = _VECTOR_TO_AGENT.get(vector)
            if not agent_class_name:
                logger.debug("Unknown vector: %s", vector)
                continue

            try:
                agent = self._instantiate_agent(agent_class_name)
                cases = await agent.run()
                # Apply mode limit
                selected = cases[:limit]
                all_cases.extend(selected)
                logger.debug("Planned %d cases from %s", len(selected), agent_class_name)
            except Exception as exc:
                logger.warning("Could not plan for %s: %s", agent_class_name, exc)

        logger.info("Attack plan: %d total cases (mode=%s)", len(all_cases), mode)
        return all_cases

    def _instantiate_agent(self, class_name: str) -> BaseAgent:
        """Dynamically import and instantiate an agent by class name."""
        import importlib

        module_map = {
            "JailbreakAgent": ("aegis.agents.jailbreak_agent", "JailbreakAgent"),
            "PromptInjectionAgent": (
                "aegis.agents.prompt_injection_agent",
                "PromptInjectionAgent",
            ),
            "DataExfiltrationAgent": (
                "aegis.agents.data_exfiltration_agent",
                "DataExfiltrationAgent",
            ),
            "EncodingAgent": ("aegis.agents.encoding_agent", "EncodingAgent"),
            "ContextPoisoningAgent": (
                "aegis.agents.context_poisoning_agent",
                "ContextPoisoningAgent",
            ),
        }

        if class_name not in module_map:
            raise ValueError(f"Unknown agent: {class_name}")

        module_path, cls_name = module_map[class_name]
        module = importlib.import_module(module_path)
        cls = getattr(module, cls_name)
        return cast(BaseAgent, cls(context=self.context))
