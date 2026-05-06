"""Database persistence tests."""

from __future__ import annotations

from datetime import datetime

from aegis.core.models import SessionSummary
from aegis.db import database
from aegis.db.repositories import SessionRepository
from aegis.services.runner import Runner


def _reset_database_cache() -> None:
    database._engine = None
    database._SessionFactory = None


def test_runner_persist_session_initializes_database(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "aegis.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    _reset_database_cache()

    summary = SessionSummary(
        session_id="session-123",
        target_url="http://localhost:9000/chat",
        provider="openai",
        model="gpt-4o-mini",
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        status="completed",
        total_attacks=1,
        passed=1,
        warnings=0,
        failed=0,
        total_tokens=42,
        estimated_cost=0.001,
        overall_risk_score=12.5,
    )

    Runner()._persist_session(summary)

    factory = database.get_session_factory()
    with factory() as db:
        persisted = SessionRepository(db).get("session-123")

    assert persisted is not None
    assert persisted.status == "completed"
    assert persisted.total_attacks == 1

    _reset_database_cache()
