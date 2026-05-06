"""FastAPI mock LLM target application."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from aegis import __version__
from aegis.mock_target.scenarios import ScenarioEngine


class ChatRequest(BaseModel):
    """Incoming chat request."""

    message: str
    history: list[dict[str, Any]] = []
    model: Optional[str] = None


class TokenUsage(BaseModel):
    """Token usage response."""

    prompt: int
    completion: int


class ChatResponse(BaseModel):
    """Chat response matching Aegis TargetClient expected format."""

    response: str
    model: str
    tokens: TokenUsage


def create_app(mode: str = "vulnerable") -> FastAPI:
    """Create and configure the mock target FastAPI application.

    Args:
        mode: Scenario mode - secure, vulnerable, or random.

    Returns:
        Configured FastAPI application.
    """
    engine = ScenarioEngine(mode=mode)

    mock_app = FastAPI(
        title="Aegis AI Mock LLM Target",
        description=(
            f"Mock LLM endpoint for red-team testing (mode: {mode}). "
            "This server simulates a vulnerable or secure LLM."
        ),
        version=__version__,
    )

    @mock_app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok", "mode": mode}

    @mock_app.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest) -> ChatResponse:
        """Process a chat request and return a mocked LLM response."""
        result = engine.respond(request.message, request.history)
        return ChatResponse(
            response=str(result["response"]),
            model=str(result["model"]),
            tokens=TokenUsage(
                prompt=int(result["tokens"]["prompt"]),  # type: ignore[index]
                completion=int(result["tokens"]["completion"]),  # type: ignore[index]
            ),
        )

    @mock_app.post("/v1/chat/completions")
    async def openai_chat(body: dict[str, Any]) -> dict[str, Any]:
        """OpenAI-compatible chat completions endpoint."""
        messages: list[dict[str, Any]] = body.get("messages", [])
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        result = engine.respond(user_message)
        response_text = str(result["response"])
        tokens: dict[str, int] = result["tokens"]  # type: ignore[assignment]

        return {
            "id": "chatcmpl-mock-001",
            "object": "chat.completion",
            "model": result["model"],
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": response_text},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": tokens["prompt"],
                "completion_tokens": tokens["completion"],
                "total_tokens": tokens["prompt"] + tokens["completion"],
            },
        }

    return mock_app
