"""Mock TargetClient for use in tests - no HTTP calls."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from aegis.core.exceptions import RateLimitError, TargetDownError
from aegis.core.models import AttackCase, AttackResult


class MockTargetClient:
    """Replaces TargetClient in tests by returning pre-canned AttackResult objects.

    Configure responses via the `response_map` dict (attack_id -> AttackResult)
    or set `default_response` for all calls.
    """

    def __init__(
        self,
        default_response: AttackResult | None = None,
        response_map: dict[str, AttackResult] | None = None,
        raise_on_send: Exception | None = None,
    ) -> None:
        self.default_response = default_response
        self.response_map = response_map or {}
        self.raise_on_send = raise_on_send
        self.call_log: list[AttackCase] = []

    async def send(self, attack_case: AttackCase) -> AttackResult:
        """Return a pre-canned response without making any HTTP call."""
        self.call_log.append(attack_case)

        if self.raise_on_send:
            raise self.raise_on_send

        if attack_case.attack_id in self.response_map:
            return self.response_map[attack_case.attack_id]

        if self.default_response:
            # Return default with updated attack_id
            return self.default_response.model_copy(
                update={"attack_id": attack_case.attack_id, "prompt": attack_case.prompt}
            )

        # Sensible default: a clean refusal
        return AttackResult(
            attack_id=attack_case.attack_id,
            agent_name=attack_case.agent_name,
            category=attack_case.category,
            prompt=attack_case.prompt,
            response=(
                "I'm sorry, I can't help with that. Is there something else I can assist you with?"
            ),
            status_code=200,
            latency_ms=100.0,
            prompt_tokens=len(attack_case.prompt.split()),
            completion_tokens=15,
            estimated_cost=0.000005,
            timestamp=datetime.utcnow(),
        )

    async def close(self) -> None:
        """No-op for interface compatibility."""

    async def __aenter__(self) -> "MockTargetClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        pass


class DownMockTargetClient(MockTargetClient):
    """Always raises TargetDownError."""

    async def send(self, attack_case: AttackCase) -> AttackResult:
        raise TargetDownError("Mock target is down")


class RateLimitMockTargetClient(MockTargetClient):
    """Returns a rate limit error on first N calls, then succeeds."""

    def __init__(self, fail_count: int = 1, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.fail_count = fail_count
        self._call_count = 0

    async def send(self, attack_case: AttackCase) -> AttackResult:
        self._call_count += 1
        if self._call_count <= self.fail_count:
            raise RateLimitError("Rate limited", retry_after=0.01)
        return await super().send(attack_case)
