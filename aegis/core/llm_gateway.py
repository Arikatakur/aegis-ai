"""LLM Gateway for Aegis AI core - wraps LiteLLM for provider-agnostic completions."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class LLMGateway:
    """Thin async wrapper around LiteLLM for multi-provider LLM access.

    Handles provider routing and never logs API keys.
    """

    async def complete(
        self,
        prompt: str,
        model: str,
        api_key: str = "",
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        """Send a completion request via LiteLLM.

        Args:
            prompt: User message to send.
            model: LiteLLM model string (e.g. "openai/gpt-4o-mini").
            api_key: Provider API key (never logged).
            system_prompt: Optional system message.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.

        Returns:
            Dict with keys: text, prompt_tokens, completion_tokens.
        """
        try:
            import litellm  # type: ignore[import]

            messages: list[dict[str, str]] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            kwargs: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if api_key:
                kwargs["api_key"] = api_key

            response = await litellm.acompletion(**kwargs)  # type: ignore[attr-defined]

            text = response.choices[0].message.content or ""
            usage = response.usage or {}
            prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
            completion_tokens = getattr(usage, "completion_tokens", 0) or 0

            return {
                "text": text,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            }

        except Exception as exc:
            # Log without revealing keys
            logger.warning("LLMGateway completion failed: %s", type(exc).__name__)
            raise
