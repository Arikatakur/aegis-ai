"""SQLAlchemy ORM models for Aegis AI database."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from aegis.db.database import Base


class DBSession(Base):
    """Database model for a red-team session."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    target_url: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    total_attacks: Mapped[int] = mapped_column(Integer, default=0)
    passed: Mapped[int] = mapped_column(Integer, default=0)
    warnings: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    overall_risk_score: Mapped[float] = mapped_column(Float, default=0.0)


class DBAttackResult(Base):
    """Database model for an individual attack result."""

    __tablename__ = "attack_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    attack_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    response: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status_code: Mapped[int] = mapped_column(Integer, default=200)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )


class DBValidationResult(Base):
    """Database model for a validation result."""

    __tablename__ = "validation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    attack_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    result: Mapped[str] = mapped_column(String(16), nullable=False)  # PASS/WARNING/FAIL
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    evidence: Mapped[str] = mapped_column(Text, nullable=False, default="")
    owasp_mappings: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    validator_name: Mapped[str] = mapped_column(String(64), nullable=False, default="")


class DBReport(Base):
    """Database model for a generated report."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    format: Mapped[str] = mapped_column(String(16), nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
