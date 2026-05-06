"""Jailbreak attack agent - tests role manipulation and instruction-override techniques."""

from __future__ import annotations

from aegis.agents.base_agent import BaseAgent
from aegis.core.models import AttackCase


class JailbreakAgent(BaseAgent):
    """Generates jailbreak attack cases from templates.

    Tests: role manipulation, DAN-style (educational), developer mode simulation,
    hypothetical framing, and instruction conflict.
    """

    name = "jailbreak"

    async def run(self) -> list[AttackCase]:
        """Load jailbreak templates and return AttackCase objects."""
        templates = self.load_templates("jailbreak")
        return [self._template_to_attack_case(t) for t in templates]
