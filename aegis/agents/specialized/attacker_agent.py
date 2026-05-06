"""Attacker agent - execution wrapper for running individual attack cases."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aegis.core.models import AttackCase, AttackResult

if TYPE_CHECKING:
    from aegis.execution.target_client import TargetClient

logger = logging.getLogger(__name__)


class AttackerAgent:
    """Wraps the TargetClient to execute a single AttackCase.

    Provides retry logic and result normalisation on top of the raw client.
    """

    def __init__(self, target_client: "TargetClient", max_retries: int = 2) -> None:
        self.target_client = target_client
        self.max_retries = max_retries

    async def execute(self, case: AttackCase) -> AttackResult:
        """Execute an attack case, retrying on transient failures.

        Args:
            case: The AttackCase to execute.

        Returns:
            AttackResult from the target.
        """
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                result = await self.target_client.send(case)
                logger.debug(
                    "AttackerAgent executed %s (attempt %d/%d)",
                    case.attack_id,
                    attempt + 1,
                    self.max_retries + 1,
                )
                return result
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "AttackerAgent attempt %d failed for %s: %s",
                    attempt + 1,
                    case.attack_id,
                    exc,
                )

        raise RuntimeError(
            f"All {self.max_retries + 1} attempts failed for {case.attack_id}"
        ) from last_exc
