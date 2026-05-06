"""Session management for Aegis AI red-team runs."""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from aegis.core.context_manager import ContextManager


class Session:
    """Represents a single red-team session with lifecycle management."""

    def __init__(self, reports_dir: str = "reports") -> None:
        self.session_id: str = str(uuid.uuid4())
        self.started_at: datetime | None = None
        self.finished_at: datetime | None = None
        self.status: str = "pending"
        self.reports_dir = reports_dir
        self.context = ContextManager()

    def start(self) -> None:
        """Mark the session as started."""
        self.started_at = datetime.utcnow()
        self.status = "running"

    def finish(self, status: str = "completed") -> None:
        """Mark the session as finished."""
        self.finished_at = datetime.utcnow()
        self.status = status

    def get_report_dir(self) -> Path:
        """Return the report output directory for this session."""
        report_path = Path(self.reports_dir) / self.session_id
        report_path.mkdir(parents=True, exist_ok=True)
        return report_path

    @property
    def duration_seconds(self) -> float:
        """Return elapsed duration in seconds, or 0 if not started."""
        if not self.started_at:
            return 0.0
        end = self.finished_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()
