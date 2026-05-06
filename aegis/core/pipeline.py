"""Orchestration pipeline for Aegis AI red-team sessions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from aegis.core.context_manager import ContextManager
from aegis.core.models import SessionSummary
from aegis.core.session import Session

if TYPE_CHECKING:
    from aegis.config.target_config import TargetConfig

logger = logging.getLogger(__name__)


class Pipeline:
    """Orchestrates the six phases of a red-team session.

    Phases:
        1. recon   - Probe target to understand guardrails
        2. plan    - Select attack vectors based on recon
        3. execute - Fire attack cases against target
        4. validate - Judge results for failures/leakage
        5. score   - Compute risk scores
        6. report  - Export findings
    """

    def __init__(self, target_config: "TargetConfig", session: Session) -> None:
        self.target_config = target_config
        self.session = session
        self.context: ContextManager = session.context

    async def run(self, mode: str = "standard") -> SessionSummary:
        """Execute all pipeline phases in order.

        Args:
            mode: Run mode - quick, standard, or deep.

        Returns:
            SessionSummary with aggregated results.
        """
        self.session.start()
        logger.info("Pipeline starting - session %s", self.session.session_id)

        try:
            await self._phase_recon()
            await self._phase_plan(mode)
            attack_results = await self._phase_execute()
            await self._phase_validate(attack_results)
            risk_score = await self._phase_score()
            report_path = await self._phase_report(risk_score)

            self.session.finish("completed")
            logger.info("Pipeline completed - report at %s", report_path)

        except Exception as exc:
            self.session.finish("failed")
            logger.error("Pipeline failed: %s", exc)
            raise

        return self._build_summary(risk_score if "risk_score" in dir() else 0.0)

    async def _phase_recon(self) -> None:
        """Phase 1: Reconnaissance - probe target guardrails."""
        logger.info("[Phase 1/6] Recon")
        from aegis.agents.recon_agent import ReconAgent
        from aegis.execution.target_client import TargetClient

        client = TargetClient(self.target_config)
        agent = ReconAgent(context=self.context, target_client=client)
        findings = await agent.run_recon()
        await self.context.set_recon_findings(findings)

    async def _phase_plan(self, mode: str) -> None:
        """Phase 2: Planning - select attack agents."""
        logger.info("[Phase 2/6] Plan")
        from aegis.agents.attack_planner import AttackPlanner

        planner = AttackPlanner(context=self.context)
        attack_cases = await planner.plan(mode=mode)
        self.context.metadata["planned_attacks"] = [a.model_dump() for a in attack_cases]
        self.context.metadata["attack_objects"] = attack_cases

    async def _phase_execute(self) -> list[Any]:
        """Phase 3: Execution - run attack cases."""
        logger.info("[Phase 3/6] Execute")
        from aegis.execution.executor import AsyncExecutor

        attack_cases = self.context.metadata.get("attack_objects", [])
        executor = AsyncExecutor(
            target_config=self.target_config,
            context=self.context,
            concurrency=self.target_config.concurrency,
        )
        results = await executor.execute_batch(attack_cases)
        for r in results:
            await self.context.add_attack_result(r)
        return results

    async def _phase_validate(self, attack_results: list[Any]) -> None:
        """Phase 4: Validation - judge results."""
        logger.info("[Phase 4/6] Validate")
        from aegis.validation.validator import Validator

        validator = Validator()
        for result in attack_results:
            vr = await validator.validate(result)
            await self.context.add_validation_result(vr)

    async def _phase_score(self) -> float:
        """Phase 5: Risk scoring."""
        logger.info("[Phase 5/6] Score")
        from aegis.reporting.risk_scoring import RiskScoring

        scorer = RiskScoring()
        score = scorer.calculate(self.context.validation_results)
        self.context.metadata["risk_score"] = score
        return score

    async def _phase_report(self, risk_score: float) -> str:
        """Phase 6: Report generation."""
        logger.info("[Phase 6/6] Report")
        from aegis.reporting.report_builder import ReportBuilder
        from aegis.reporting.export import export_json, export_markdown, export_txt

        builder = ReportBuilder(
            session=self.session,
            context=self.context,
            target_config=self.target_config,
            risk_score=risk_score,
        )
        report_data = builder.build()

        report_dir = self.session.get_report_dir()
        export_json(report_data, report_dir / "report.json")
        export_txt(report_data, report_dir / "report.txt")
        export_markdown(report_data, report_dir / "report.md")

        return str(report_dir)

    def _build_summary(self, risk_score: float) -> SessionSummary:
        """Assemble a SessionSummary from context data."""
        ctx_summary = self.context.get_summary()
        return SessionSummary(
            session_id=self.session.session_id,
            target_url=self.target_config.endpoint,
            provider=self.target_config.provider,
            model=self.target_config.model,
            started_at=self.session.started_at or __import__("datetime").datetime.utcnow(),
            finished_at=self.session.finished_at,
            status=self.session.status,
            total_attacks=ctx_summary["total_attacks"],
            passed=ctx_summary["passed"],
            warnings=ctx_summary["warnings"],
            failed=ctx_summary["failed"],
            total_tokens=self.context.token_usage.get("total_tokens", 0),
            estimated_cost=ctx_summary.get("estimated_cost", 0.0),
            overall_risk_score=risk_score,
        )
