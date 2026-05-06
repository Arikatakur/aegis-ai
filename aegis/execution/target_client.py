"""HTTP client for communicating with the target LLM endpoint."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

import httpx

from aegis.core.exceptions import (
    InvalidTargetResponseError,
    RateLimitError,
    TargetDownError,
)
from aegis.core.models import AttackCase, AttackResult

if TYPE_CHECKING:
    from aegis.config.target_config import TargetConfig

logger = logging.getLogger(__name__)

# Cost per 1K tokens (rough estimate for gpt-4o-mini)
_COST_PER_1K_PROMPT = 0.00015
_COST_PER_1K_COMPLETION = 0.00060


class TargetClient:
    """Async HTTP client that sends AttackCase prompts to the target LLM.

    Supports OpenAI-compatible API format. Never logs API keys.
    """

    def __init__(self, config: TargetConfig) -> None:
        self.config = config
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers: dict[str, str] = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                headers=headers,
            )
        return self._client

    async def send(self, attack_case: AttackCase) -> AttackResult:
        """Send an attack prompt to the target and return a normalised result.

        Args:
            attack_case: The attack to execute.

        Returns:
            AttackResult with response text, latency, and token usage.

        Raises:
            TargetDownError: If the target is unreachable.
            RateLimitError: If the target returns HTTP 429.
            InvalidTargetResponseError: If the response is malformed.
        """
        client = self._get_client()
        payload = self._build_payload(attack_case.prompt)

        t0 = time.monotonic()
        try:
            response = await client.post(self.config.endpoint, json=payload)
        except httpx.ConnectError as exc:
            raise TargetDownError(f"Cannot reach target at {self.config.endpoint}: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise TargetDownError(f"Request timed out: {exc}") from exc

        latency_ms = (time.monotonic() - t0) * 1000

        if response.status_code == 429:
            retry_after = float(response.headers.get("Retry-After", "0"))
            raise RateLimitError("Rate limit exceeded", retry_after=retry_after)

        if response.status_code >= 500:
            raise InvalidTargetResponseError(f"Target returned server error {response.status_code}")

        try:
            data = response.json()
        except Exception as exc:
            raise InvalidTargetResponseError(
                f"Non-JSON response from target: {response.text[:200]}"
            ) from exc

        return self._normalise_response(attack_case, data, response.status_code, latency_ms)

    def _build_payload(self, prompt: str) -> dict[str, Any]:
        """Build OpenAI-compatible chat payload."""
        messages: list[dict[str, str]] = []
        if self.config.system_prompt:
            messages.append({"role": "system", "content": self.config.system_prompt})
        messages.append({"role": "user", "content": prompt})

        return {
            "model": self.config.model,
            "messages": messages,
            "message": prompt,  # Also include flat format for mock target
        }

    def _normalise_response(
        self,
        case: AttackCase,
        data: dict[str, Any],
        status_code: int,
        latency_ms: float,
    ) -> AttackResult:
        """Extract standard fields from various response formats."""
        # Try OpenAI chat completions format
        response_text = ""
        prompt_tokens = 0
        completion_tokens = 0

        if "choices" in data:
            choice = data["choices"][0] if data["choices"] else {}
            response_text = choice.get("message", {}).get("content", "") or choice.get("text", "")
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
        elif "response" in data:
            # Mock target / simple format
            response_text = data.get("response", "")
            tokens = data.get("tokens", {})
            prompt_tokens = tokens.get("prompt", 0)
            completion_tokens = tokens.get("completion", 0)
        else:
            response_text = str(data)

        estimated_cost = (prompt_tokens / 1000) * _COST_PER_1K_PROMPT + (
            completion_tokens / 1000
        ) * _COST_PER_1K_COMPLETION

        return AttackResult(
            attack_id=case.attack_id,
            agent_name=case.agent_name,
            category=case.category,
            prompt=case.prompt,
            response=response_text,
            status_code=status_code,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            estimated_cost=estimated_cost,
            raw_response=data,
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self) -> TargetClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
