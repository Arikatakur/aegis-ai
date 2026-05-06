"""Repository classes for Aegis AI database CRUD operations."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from aegis.core.models import AttackResult, SessionSummary, ValidationResult
from aegis.db.models import DBAttackResult, DBReport, DBSession, DBValidationResult


class SessionRepository:
    """CRUD for session records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, summary: SessionSummary) -> DBSession:
        """Create a new session record from a SessionSummary."""
        db_session = DBSession(
            session_id=summary.session_id,
            target_url=summary.target_url,
            provider=summary.provider,
            model=summary.model,
            started_at=summary.started_at,
            finished_at=summary.finished_at,
            status=summary.status,
            total_attacks=summary.total_attacks,
            passed=summary.passed,
            warnings=summary.warnings,
            failed=summary.failed,
            total_tokens=summary.total_tokens,
            estimated_cost=summary.estimated_cost,
            overall_risk_score=summary.overall_risk_score,
        )
        self.db.add(db_session)
        self.db.flush()
        return db_session

    def get(self, session_id: str) -> DBSession | None:
        """Return a session by session_id."""
        return (
            self.db.query(DBSession)
            .filter(DBSession.session_id == session_id)
            .first()
        )

    def list_all(self) -> list[DBSession]:
        """Return all sessions ordered by started_at descending."""
        return (
            self.db.query(DBSession)
            .order_by(DBSession.started_at.desc())
            .all()
        )

    def update_status(self, session_id: str, status: str) -> None:
        """Update session status."""
        session = self.get(session_id)
        if session:
            session.status = status
            self.db.flush()

    def delete(self, session_id: str) -> None:
        """Delete a session record."""
        session = self.get(session_id)
        if session:
            self.db.delete(session)
            self.db.flush()


class AttackRepository:
    """CRUD for attack result records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, session_id: str, result: AttackResult) -> DBAttackResult:
        """Create a new attack result record."""
        db_result = DBAttackResult(
            session_id=session_id,
            attack_id=result.attack_id,
            agent_name=result.agent_name,
            category=result.category,
            prompt=result.prompt,
            response=result.response,
            status_code=result.status_code,
            latency_ms=result.latency_ms,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            estimated_cost=result.estimated_cost,
            timestamp=result.timestamp,
        )
        self.db.add(db_result)
        self.db.flush()
        return db_result

    def list_for_session(self, session_id: str) -> list[DBAttackResult]:
        """Return all attack results for a session."""
        return (
            self.db.query(DBAttackResult)
            .filter(DBAttackResult.session_id == session_id)
            .all()
        )

    def get(self, attack_id: str) -> DBAttackResult | None:
        """Return an attack result by attack_id."""
        return (
            self.db.query(DBAttackResult)
            .filter(DBAttackResult.attack_id == attack_id)
            .first()
        )


class ValidationRepository:
    """CRUD for validation result records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, session_id: str, result: ValidationResult) -> DBValidationResult:
        """Create a new validation result record."""
        db_result = DBValidationResult(
            session_id=session_id,
            attack_id=result.attack_id,
            result=result.result.value,
            confidence=result.confidence,
            evidence=result.evidence,
            owasp_mappings=json.dumps(result.owasp_mappings),
            severity=result.severity,
            validator_name=result.validator_name,
        )
        self.db.add(db_result)
        self.db.flush()
        return db_result

    def list_for_session(self, session_id: str) -> list[DBValidationResult]:
        """Return all validation results for a session."""
        return (
            self.db.query(DBValidationResult)
            .filter(DBValidationResult.session_id == session_id)
            .all()
        )


class ReportRepository:
    """CRUD for report records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, session_id: str, fmt: str, path: str) -> DBReport:
        """Create a new report record."""
        db_report = DBReport(
            session_id=session_id,
            format=fmt,
            path=path,
            created_at=datetime.utcnow(),
        )
        self.db.add(db_report)
        self.db.flush()
        return db_report

    def list_for_session(self, session_id: str) -> list[DBReport]:
        """Return all reports for a session."""
        return (
            self.db.query(DBReport)
            .filter(DBReport.session_id == session_id)
            .all()
        )

    def get_latest(self, session_id: str, fmt: str) -> DBReport | None:
        """Return the latest report of a given format for a session."""
        return (
            self.db.query(DBReport)
            .filter(DBReport.session_id == session_id, DBReport.format == fmt)
            .order_by(DBReport.created_at.desc())
            .first()
        )
