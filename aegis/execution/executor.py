"""Async executor for running batches of attack cases with concurrency control."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from aegis.core.models import AttackCase, AttackResult
from aegis.execution.rate_limiter import RateLimiter
from aegis.execution.target_client import TargetClient

if TYPE_CHECKING:
    from aegis.config.target_config import TargetConfig
    from aegis.core.context_manager import ContextManager

logger = logging.getLogger(__name__)


class AsyncExecutor:
    """Executes batches of attack cases concurrently with a semaphore.

    Shows a Rich progress bar during execution and stores results.
    """

    def __init__(
        self,
        target_config: TargetConfig,
        context: ContextManager,
        concurrency: int = 5,
    ) -> None:
        self.target_config = target_config
        self.context = context
        self.concurrency = concurrency
        self.rate_limiter = RateLimiter(max_concurrency=concurrency)

    async def execute_batch(self, attack_cases: list[AttackCase]) -> list[AttackResult]:
        """Execute all attack cases concurrently.

        Args:
            attack_cases: Cases to execute.

        Returns:
            List of AttackResult objects (same order as input).
        """
        if not attack_cases:
            return []

        results: list[AttackResult | None] = [None] * len(attack_cases)

        async with TargetClient(self.target_config) as client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold cyan]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                transient=True,
            ) as progress:
                task_id = progress.add_task(
                    f"Executing {len(attack_cases)} attacks", total=len(attack_cases)
                )

                semaphore = asyncio.Semaphore(self.concurrency)

                async def run_one(idx: int, case: AttackCase) -> None:
                    async with semaphore:
                        try:
                            result = await client.send(case)
                        except Exception as exc:
                            logger.warning("Attack %s failed: %s", case.attack_id, exc)

                            result = AttackResult(
                                attack_id=case.attack_id,
                                agent_name=case.agent_name,
                                category=case.category,
                                prompt=case.prompt,
                                response=f"[ERROR] {exc}",
                                status_code=0,
                            )
                        results[idx] = result
                        progress.advance(task_id)

                await asyncio.gather(*[run_one(i, case) for i, case in enumerate(attack_cases)])

        return [r for r in results if r is not None]
