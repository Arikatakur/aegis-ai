"""Report builder that assembles all session data into a structured report."""

from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING, Any

from aegis import __version__
from aegis.reporting.owasp_mapper import OWASPMapper

if TYPE_CHECKING:
    from aegis.config.target_config import TargetConfig
    from aegis.core.context_manager import ContextManager
    from aegis.core.session import Session

# Regex to scrub API key patterns from report text
_API_KEY_RE = re.compile(
    r"(sk-|sk_|Bearer\s+)[A-Za-z0-9_\-]{20,}",
    re.IGNORECASE,
)


def _scrub_secrets(text: str) -> str:
    """Replace API key patterns with redacted placeholder."""
    return _API_KEY_RE.sub("[REDACTED]", text)


class ReportBuilder:
    """Assembles a complete report data structure from session and context data.

    All API keys are scrubbed from the output.
    """

    def __init__(
        self,
        session: Session,
        context: ContextManager,
        target_config: TargetConfig,
        risk_score: float = 0.0,
    ) -> None:
        self.session = session
        self.context = context
        self.target_config = target_config
        self.risk_score = risk_score
        self.owasp_mapper = OWASPMapper()

    def build(self) -> dict[str, Any]:
        """Build the complete report dictionary.

        Returns:
            Report data dict suitable for JSON/Markdown export.
        """
        ctx_summary = self.context.get_summary()
        from aegis.reporting.risk_scoring import RiskScoring

        scorer = RiskScoring()
        risk_level = scorer.get_level(self.risk_score)

        owasp_summary = self.owasp_mapper.summarise_findings(self.context.validation_results)

        findings = self._build_findings()

        report: dict[str, Any] = {
            "meta": {
                "tool": "Aegis AI",
                "version": __version__,
                "generated_at": datetime.utcnow().isoformat(),
                "session_id": self.session.session_id,
            },
            "target": {
                "endpoint": self.target_config.endpoint,
                "provider": self.target_config.provider,
                "model": self.target_config.model,
                "api_key": "[REDACTED]",
                "mode": self.target_config.mode,
            },
            "executive_summary": self._executive_summary(ctx_summary, risk_level),
            "risk": {
                "score": self.risk_score,
                "level": risk_level,
                "description": self._risk_description(risk_level),
            },
            "owasp_mapping": owasp_summary,
            "statistics": ctx_summary,
            "findings": findings,
            "token_usage": self.context.token_usage,
            "estimated_cost": ctx_summary.get("estimated_cost", 0.0),
            "recommendations": self._recommendations(risk_level, owasp_summary),
        }

        # Scrub any accidentally included secrets from string values
        return self._deep_scrub(report)

    def _executive_summary(self, ctx_summary: dict[str, Any], risk_level: str) -> str:
        return (
            f"Aegis AI conducted an automated red-team assessment against "
            f"{self.target_config.endpoint} using the {self.target_config.model} model. "
            f"A total of {ctx_summary['total_attacks']} attack cases were executed. "
            f"{ctx_summary['failed']} resulted in confirmed failures, "
            f"{ctx_summary['warnings']} raised warnings, and "
            f"{ctx_summary['passed']} passed. "
            f"The overall risk level is assessed as [bold]{risk_level}[/bold] "
            f"with a score of {self.risk_score:.1f}/100."
        )

    def _build_findings(self) -> list[dict[str, Any]]:
        """Build per-attack finding entries."""
        findings = []
        vr_by_id = {vr.attack_id: vr for vr in self.context.validation_results}

        for ar in self.context.attack_results:
            vr = vr_by_id.get(ar.attack_id)
            finding: dict[str, Any] = {
                "attack_id": ar.attack_id,
                "agent": ar.agent_name,
                "category": ar.category,
                "prompt": ar.prompt,
                "response": ar.response[:1000],
                "latency_ms": ar.latency_ms,
                "validation_status": vr.result.value if vr else "UNKNOWN",
                "confidence": vr.confidence if vr else 0.0,
                "evidence": vr.evidence if vr else "",
                "owasp": vr.owasp_mappings if vr else [],
            }
            findings.append(finding)
        return findings

    def _recommendations(self, risk_level: str, owasp_summary: dict[str, Any]) -> list[str]:
        """Generate recommendations based on risk level and OWASP findings."""
        recs = []
        if "LLM01" in owasp_summary:
            recs.append(
                "Implement input sanitisation and prompt injection detection "
                "before passing user content to the LLM."
            )
        if "LLM07" in owasp_summary:
            recs.append(
                "Ensure system prompts are not exposed to users. "
                "Use output filtering to detect accidental disclosure."
            )
        if "LLM02" in owasp_summary:
            recs.append(
                "Audit what sensitive data the model has access to. "
                "Apply need-to-know restrictions on context injected into prompts."
            )
        if "LLM04" in owasp_summary:
            recs.append(
                "Validate and sanitise all documents before including them in RAG context. "
                "Consider adversarial document detection."
            )
        if risk_level in ("High", "Critical"):
            recs.append(
                "This system shows significant vulnerabilities. "
                "Do not expose it to untrusted users until mitigations are in place."
            )
        if not recs:
            recs.append(
                "No critical vulnerabilities detected. "
                "Continue periodic red-teaming as the model or application evolves."
            )
        return recs

    def _risk_description(self, risk_level: str) -> str:
        descriptions = {
            "Critical": (
                "The system is critically vulnerable and must not be deployed without "
                "immediate remediation."
            ),
            "High": "The system has significant security weaknesses requiring urgent attention.",
            "Medium": (
                "The system shows moderate vulnerabilities that should be addressed before "
                "wide deployment."
            ),
            "Low": "The system appears relatively robust but continuous monitoring is recommended.",
        }
        return descriptions.get(risk_level, "")

    def _deep_scrub(self, obj: Any) -> Any:
        """Recursively scrub secrets from all string values in a data structure."""
        if isinstance(obj, str):
            return _scrub_secrets(obj)
        elif isinstance(obj, dict):
            return {k: self._deep_scrub(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_scrub(item) for item in obj]
        return obj
