"""Rate limiter with exponential backoff and concurrency control."""

from __future__ import annotations

import asyncio
import logging
import random

from aegis.core.exceptions import RateLimitError

logger = logging.getLogger(__name__)


class RateLimiter:
    """Handles HTTP 429 responses with exponential backoff and asyncio.Semaphore.

    Also provides a context manager for concurrency control.
    """

    def __init__(
        self,
        max_concurrency: int = 5,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
    ) -> None:
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    async def execute_with_retry(self, coro_fn: object, *args: object, **kwargs: object) -> object:
        """Execute an async callable with rate-limit retry logic.

        Args:
            coro_fn: Async callable to execute.
            *args: Positional arguments for the callable.
            **kwargs: Keyword arguments for the callable.

        Returns:
            The return value of coro_fn(*args, **kwargs).

        Raises:
            RateLimitError: If max retries are exhausted.
        """
        import asyncio as _asyncio

        for attempt in range(self.max_retries + 1):
            async with self.semaphore:
                try:
                    return await coro_fn(*args, **kwargs)  # type: ignore[operator]
                except RateLimitError as exc:
                    if attempt >= self.max_retries:
                        raise
                    delay = self._backoff_delay(attempt, exc.retry_after)
                    logger.info(
                        "Rate limited. Retry %d/%d after %.1fs",
                        attempt + 1,
                        self.max_retries,
                        delay,
                    )
                    await _asyncio.sleep(delay)
        raise RateLimitError("Max retries exceeded")

    def _backoff_delay(self, attempt: int, retry_after: float) -> float:
        """Calculate backoff delay with jitter."""
        if retry_after > 0:
            return retry_after
        # Exponential backoff: 1s, 2s, 4s... with ±25% jitter
        base = min(self.base_delay * (2**attempt), self.max_delay)
        jitter = base * 0.25 * (random.random() * 2 - 1)
        return max(0.1, base + jitter)
