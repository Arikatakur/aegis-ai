"""Abstract base class for all Aegis AI attack agents."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

from aegis.core.exceptions import TemplateLoadError
from aegis.core.models import AttackCase

if TYPE_CHECKING:
    from aegis.core.context_manager import ContextManager

logger = logging.getLogger(__name__)

# Path to attack template data directory
_TEMPLATES_DIR = Path(__file__).parent.parent / "data" / "attack_templates"


class BaseAgent(ABC):
    """Abstract base class for all red-team attack agents.

    Subclasses implement `run()` to generate AttackCase objects.
    """

    name: str = "base"

    def __init__(self, context: ContextManager) -> None:
        self.context = context

    @abstractmethod
    async def run(self) -> list[AttackCase]:
        """Generate attack cases for this agent's category.

        Returns:
            List of AttackCase objects ready for execution.
        """

    def load_templates(self, category: str) -> list[dict[str, Any]]:
        """Load attack templates from the data directory.

        Args:
            category: Template file name without extension (e.g. "jailbreak").

        Returns:
            List of template dicts.

        Raises:
            TemplateLoadError: If the template file cannot be read or parsed.
        """
        template_path = _TEMPLATES_DIR / f"{category}.json"
        if not template_path.exists():
            raise TemplateLoadError(f"Template not found: {template_path}")
        try:
            with template_path.open(encoding="utf-8") as fh:
                data = json.load(fh)
            if not isinstance(data, list):
                raise TemplateLoadError(f"Expected list in {template_path}, got {type(data)}")
            return data
        except json.JSONDecodeError as exc:
            raise TemplateLoadError(f"JSON parse error in {template_path}: {exc}") from exc

    def _template_to_attack_case(self, template: dict[str, Any]) -> AttackCase:
        """Convert a raw template dict to an AttackCase."""
        return AttackCase(
            attack_id=template.get("id", ""),
            agent_name=self.name,
            category=template.get("category", self.name),
            severity=template.get("severity", "Medium"),
            prompt=template.get("prompt", ""),
            owasp_mappings=template.get("owasp", []),
            expected_failure=template.get("expected_failure_type", ""),
            metadata={
                "subcategory": template.get("subcategory", ""),
                "description": template.get("description", ""),
            },
        )
