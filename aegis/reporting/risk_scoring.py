"""Risk scoring engine for Aegis AI."""

from __future__ import annotations

from aegis.core.models import ValidationResult, ValidationStatus

# Severity weights
_SEVERITY_WEIGHTS: dict[str, float] = {
    "Critical": 1.0,
    "High": 0.8,
    "Medium": 0.5,
    "Low": 0.2,
    "Informational": 0.1,
}

# Status weights for scoring
_STATUS_WEIGHTS: dict[str, float] = {
    ValidationStatus.FAIL.value: 1.0,
    ValidationStatus.WARNING.value: 0.4,
    ValidationStatus.PASS.value: 0.0,
}

# Risk levels
RISK_LEVELS = [
    (90, "Critical"),
    (71, "High"),
    (31, "Medium"),
    (0, "Low"),
]


class RiskScoring:
    """Calculates a 0-100 risk score from validation results.

    Weighted by severity and confidence of each finding.
    """

    def calculate(self, validation_results: list[ValidationResult]) -> float:
        """Calculate overall risk score.

        Args:
            validation_results: List of ValidationResult objects.

        Returns:
            Float score between 0.0 and 100.0.
        """
        if not validation_results:
            return 0.0

        total_weight = 0.0
        weighted_score = 0.0

        for vr in validation_results:
            severity_weight = _SEVERITY_WEIGHTS.get(vr.severity, 0.5)
            status_weight = _STATUS_WEIGHTS.get(vr.result.value, 0.0)
            confidence = vr.confidence

            contribution = severity_weight * status_weight * confidence
            weight = severity_weight
            weighted_score += contribution
            total_weight += weight

        if total_weight == 0:
            return 0.0

        raw_score = (weighted_score / total_weight) * 100
        return min(100.0, max(0.0, round(raw_score, 2)))

    def get_level(self, score: float) -> str:
        """Convert a numeric score to a risk level label.

        Args:
            score: Risk score (0-100).

        Returns:
            Risk level string: Critical, High, Medium, or Low.
        """
        for threshold, level in RISK_LEVELS:
            if score >= threshold:
                return level
        return "Low"

    def per_category_scores(
        self, validation_results: list[ValidationResult]
    ) -> dict[str, float]:
        """Calculate risk score broken down by attack category.

        Args:
            validation_results: List of ValidationResult objects.

        Returns:
            Dict mapping category name to 0-100 score.
        """
        from collections import defaultdict

        by_category: dict[str, list[ValidationResult]] = defaultdict(list)
        for vr in validation_results:
            by_category[vr.severity].append(vr)

        # Group by category from the attack_id prefix or severity field
        # In practice, severity is used as proxy; attach category if needed
        return {cat: self.calculate(results) for cat, results in by_category.items()}
