"""Runner service - single source of truth for red-team execution.

Independent of CLI and API layers; callable from either.
"""

from __future__ import annotations

import logging

from aegis.config.target_config import TargetConfig
from aegis.core.models import SessionSummary
from aegis.core.pipeline import Pipeline
from aegis.core.session import Session

logger = logging.getLogger(__name__)


class Runner:
    """Orchestrates a complete red-team run through the Pipeline.

    This class is API/CLI-agnostic. Both the Typer CLI and the FastAPI
    routes delegate execution here.
    """

    def __init__(self, reports_dir: str = "reports") -> None:
        self.reports_dir = reports_dir

    async def run(
        self,
        target_config: TargetConfig,
        mode: str = "standard",
    ) -> SessionSummary:
        """Execute a full red-team session and return a summary.

        Args:
            target_config: Configuration for the target LLM.
            mode: Run mode - quick, standard, or deep.

        Returns:
            SessionSummary with all results and risk score.
        """
        session = Session(reports_dir=self.reports_dir)
        logger.info(
            "Runner starting session %s against %s",
            session.session_id,
            target_config.endpoint,
        )

        pipeline = Pipeline(target_config=target_config, session=session)
        summary = await pipeline.run(mode=mode)

        # Persist session to DB
        try:
            self._persist_session(summary)
        except Exception as exc:
            logger.warning("Could not persist session to DB: %s", exc)

        return summary

    def _persist_session(self, summary: SessionSummary) -> None:
        """Save the session summary to the database."""
        from aegis.db.database import get_db_session, init_db
        from aegis.db.repositories import SessionRepository

        init_db()
        with get_db_session() as db:
            repo = SessionRepository(db)
            repo.create(summary)
