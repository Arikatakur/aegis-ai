"""Combined validator: RuleValidator + optional LLMJudge."""

from __future__ import annotations

import logging

from aegis.core.models import AttackResult, ValidationResult, ValidationStatus
from aegis.validation.llm_judge import LLMJudge
from aegis.validation.rule_validator import RuleValidator

logger = logging.getLogger(__name__)


class Validator:
    """Combines rule-based and LLM-based validation.

    The rule validator runs first. If a judge model is configured, it also
    runs the LLM judge and the more severe verdict wins.
    """

    def __init__(self, judge_model: str = "", judge_api_key: str = "") -> None:
        self.rule_validator = RuleValidator()
        self.llm_judge = LLMJudge(model=judge_model, api_key=judge_api_key)

    async def validate(self, result: AttackResult) -> ValidationResult:
        """Validate an attack result.

        Args:
            result: The AttackResult to validate.

        Returns:
            ValidationResult - most severe of rule + judge verdicts.
        """
        # Rule-based validation (always runs)
        rule_result = self.rule_validator.validate(result)

        # LLM judge (optional)
        judge_result: ValidationResult | None = None
        if self.llm_judge.enabled:
            try:
                judge_result = await self.llm_judge.judge(result)
            except Exception as exc:
                logger.warning("LLM judge failed: %s", exc)

        if judge_result is None:
            return rule_result

        # Merge: most severe verdict wins
        return self._merge(rule_result, judge_result)

    def _merge(self, rule: ValidationResult, judge: ValidationResult) -> ValidationResult:
        """Combine two ValidationResults, preferring the more severe."""
        severity_rank = {
            ValidationStatus.FAIL: 2,
            ValidationStatus.WARNING: 1,
            ValidationStatus.PASS: 0,
        }

        if severity_rank[judge.result] > severity_rank[rule.result]:
            dominant = judge
        else:
            dominant = rule

        # Merge evidence
        combined_evidence = "; ".join(filter(None, [rule.evidence, judge.evidence]))
        # Merge OWASP
        combined_owasp = sorted(set(rule.owasp_mappings + judge.owasp_mappings))

        return ValidationResult(
            attack_id=dominant.attack_id,
            result=dominant.result,
            confidence=max(rule.confidence, judge.confidence),
            evidence=combined_evidence,
            owasp_mappings=combined_owasp,
            severity=dominant.severity,
            validator_name=f"{rule.validator_name}+{judge.validator_name}",
        )
