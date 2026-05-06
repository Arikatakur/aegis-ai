"""Pydantic schemas for the Aegis AI REST API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RunRequest(BaseModel):
    """Request body for POST /runs."""

    target_endpoint: str = "http://localhost:9000/chat"
    mode: str = "standard"
    categories: list[str] = []
    concurrency: int = 5
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: str = ""


class RunResponse(BaseModel):
    """Response for POST /runs."""

    job_id: str
    status: str = "pending"
    created_at: datetime


class JobStatus(BaseModel):
    """Status response for GET /runs/{job_id}."""

    job_id: str
    status: str  # pending, running, completed, failed
    progress_pct: float = 0.0
    result: dict[str, Any] | None = None
    error: str | None = None
