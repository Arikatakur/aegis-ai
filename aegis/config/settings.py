"""Aegis AI settings module - standalone to avoid circular imports."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Target LLM
    target_endpoint: str = "http://localhost:9000/chat"
    target_provider: str = "openai"
    target_model: str = "gpt-4o-mini"
    target_api_key: str = Field(default="", repr=False)

    # LiteLLM gateway
    litellm_model: str = ""
    litellm_api_key: str = Field(default="", repr=False)

    # LLM Judge
    judge_model: str = ""
    judge_api_key: str = Field(default="", repr=False)

    # Database
    database_url: str = "sqlite:///aegis.db"

    # Execution
    max_concurrency: int = 5
    request_timeout: int = 30
    max_retries: int = 3

    # Run mode
    run_mode: str = "standard"

    # Reporting
    reports_dir: str = "reports"


def get_settings() -> Settings:
    """Return a Settings instance."""
    return Settings()


__all__ = ["Settings", "get_settings"]
