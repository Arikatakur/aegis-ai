"""Encoding obfuscation attack agent."""

from __future__ import annotations

from aegis.agents.base_agent import BaseAgent
from aegis.core.models import AttackCase


class EncodingAgent(BaseAgent):
    """Generates encoding-based obfuscation attack cases from templates.

    Tests: unicode lookalikes, spaced-out instructions,
    indirect references, and obfuscated commands.
    """

    name = "encoding"

    async def run(self) -> list[AttackCase]:
        """Load encoding templates and return AttackCase objects."""
        templates = self.load_templates("encoding")
        return [self._template_to_attack_case(t) for t in templates]
