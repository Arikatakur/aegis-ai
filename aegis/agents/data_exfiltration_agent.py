"""Data exfiltration attack agent."""

from __future__ import annotations

from aegis.agents.base_agent import BaseAgent
from aegis.core.models import AttackCase


class DataExfiltrationAgent(BaseAgent):
    """Generates data exfiltration attack cases from templates.

    Tests: system prompt extraction, hidden context leakage,
    RAG context exposure, and memory leakage.
    """

    name = "data_exfiltration"

    async def run(self) -> list[AttackCase]:
        """Load data exfiltration templates and return AttackCase objects."""
        templates = self.load_templates("data_exfiltration")
        return [self._template_to_attack_case(t) for t in templates]
