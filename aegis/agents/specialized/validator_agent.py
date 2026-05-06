"""Validator agent - validates attack results using rules and optionally an LLM judge."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aegis.core.models import AttackResult, ValidationResult

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ValidatorAgent:
    """Wraps the Validator to provide an agent-style interface."""

    def __init__(self, judge_model: str = "", judge_api_key: str = "") -> None:
        self.judge_model = judge_model
        self.judge_api_key = judge_api_key

    async def validate(self, result: AttackResult) -> ValidationResult:
        """Validate an attack result.

        Args:
            result: The AttackResult to validate.

        Returns:
            ValidationResult with PASS/WARNING/FAIL verdict.
        """
        from aegis.validation.validator import Validator

        validator = Validator(
            judge_model=self.judge_model,
            judge_api_key=self.judge_api_key,
        )
        return await validator.validate(result)
