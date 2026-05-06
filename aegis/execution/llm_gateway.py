"""Thin LiteLLM wrapper for the execution layer."""

from __future__ import annotations

from aegis.core.llm_gateway import LLMGateway

# Re-export the core gateway for use within the execution package
__all__ = ["LLMGateway"]
