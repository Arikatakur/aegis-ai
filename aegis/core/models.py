"""Core Pydantic data models for Aegis AI."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ValidationStatus(StrEnum):
    """Possible outcomes for a validation check."""

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


class AttackCase(BaseModel):
    """A single attack test case to be executed against the target."""

    attack_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    category: str
    severity: str = "Medium"
    prompt: str
    owasp_mappings: list[str] = Field(default_factory=list)
    expected_failure: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class AttackResult(BaseModel):
    """Result from executing an AttackCase against the target."""

    attack_id: str
    agent_name: str
    category: str
    prompt: str
    response: str
    status_code: int = 200
    latency_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    raw_response: dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Result from validating an AttackResult."""

    attack_id: str
    result: ValidationStatus
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    evidence: str = ""
    owasp_mappings: list[str] = Field(default_factory=list)
    severity: str = "Medium"
    validator_name: str = ""


class ReconFindings(BaseModel):
    """Findings from the reconnaissance phase."""

    guardrail_strength: str = "unknown"  # none, weak, moderate, strong
    refusal_style: str = "unknown"  # polite, terse, silent, redirect
    suspected_filters: list[str] = Field(default_factory=list)
    susceptible_vectors: list[str] = Field(default_factory=list)
    recommended_agents: list[str] = Field(default_factory=list)
    raw_responses: list[dict[str, Any]] = Field(default_factory=list)


class SessionSummary(BaseModel):
    """High-level summary of a red-team session."""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_url: str = ""
    provider: str = ""
    model: str = ""
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    status: str = "pending"  # pending, running, completed, failed
    total_attacks: int = 0
    passed: int = 0
    warnings: int = 0
    failed: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    overall_risk_score: float = 0.0
