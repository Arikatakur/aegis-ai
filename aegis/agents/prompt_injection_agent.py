"""Prompt injection attack agent."""

from __future__ import annotations

from aegis.agents.base_agent import BaseAgent
from aegis.core.models import AttackCase


class PromptInjectionAgent(BaseAgent):
    """Generates prompt injection attack cases from templates.

    Tests: ignore-previous-instructions variants, context hijacking,
    instruction override, and conflicting priority attacks.
    """

    name = "prompt_injection"

    async def run(self) -> list[AttackCase]:
        """Load prompt injection templates and return AttackCase objects."""
        templates = self.load_templates("prompt_injection")
        return [self._template_to_attack_case(t) for t in templates]
