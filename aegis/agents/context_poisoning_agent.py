"""Context poisoning / RAG-focused attack agent."""

from __future__ import annotations

from aegis.agents.base_agent import BaseAgent
from aegis.core.models import AttackCase


class ContextPoisoningAgent(BaseAgent):
    """Generates context poisoning attack cases from templates.

    Tests: malicious document instructions, retrieval manipulation,
    and context priority attacks targeting RAG-augmented systems.
    """

    name = "context_poisoning"

    async def run(self) -> list[AttackCase]:
        """Load context poisoning templates and return AttackCase objects."""
        templates = self.load_templates("context_poisoning")
        return [self._template_to_attack_case(t) for t in templates]
