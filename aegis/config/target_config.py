"""Pydantic model for target LLM configuration."""

from pydantic import BaseModel, Field


class TargetConfig(BaseModel):
    """Configuration for the LLM target being tested."""

    endpoint: str = "http://localhost:9000/chat"
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: str = Field(default="", repr=False)
    timeout: int = 30
    concurrency: int = 5
    mode: str = "standard"
    system_prompt: str = "You are a helpful assistant."

    @property
    def masked_key(self) -> str:
        """Return the API key with only the last 4 characters visible."""
        if not self.api_key or len(self.api_key) <= 4:
            return "****"
        return f"{'*' * (len(self.api_key) - 4)}{self.api_key[-4:]}"

    def model_post_init(self, __context: object) -> None:
        """Validate mode after initialization."""
        valid_modes = {"quick", "standard", "deep"}
        if self.mode not in valid_modes:
            raise ValueError(f"mode must be one of {valid_modes}, got '{self.mode}'")
