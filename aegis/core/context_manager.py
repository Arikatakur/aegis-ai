"""Blackboard-pattern context manager for sharing state between pipeline phases."""

from __future__ import annotations

import asyncio
from typing import Any

from aegis.core.models import (
    AttackResult,
    ReconFindings,
    ValidationResult,
)


class ContextManager:
    """Thread-safe shared context (blackboard) for a single red-team session.

    All pipeline phases read and write through this object, making it the
    single source of truth for session state.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()

        self.recon_findings: ReconFindings | None = None
        self.selected_vectors: list[str] = []
        self.attack_results: list[AttackResult] = []
        self.validation_results: list[ValidationResult] = []
        self.successful_patterns: list[str] = []
        self.failed_patterns: list[str] = []
        self.token_usage: dict[str, int] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        self.metadata: dict[str, Any] = {}

    async def set_recon_findings(self, findings: ReconFindings) -> None:
        """Store recon findings into the blackboard."""
        async with self._lock:
            self.recon_findings = findings
            self.selected_vectors = findings.susceptible_vectors.copy()

    async def add_attack_result(self, result: AttackResult) -> None:
        """Append an attack result and update token counts."""
        async with self._lock:
            self.attack_results.append(result)
            self.token_usage["prompt_tokens"] += result.prompt_tokens
            self.token_usage["completion_tokens"] += result.completion_tokens
            self.token_usage["total_tokens"] += result.prompt_tokens + result.completion_tokens

    async def add_validation_result(self, result: ValidationResult) -> None:
        """Append a validation result and track pass/fail patterns."""
        async with self._lock:
            self.validation_results.append(result)
            attack = next(
                (a for a in self.attack_results if a.attack_id == result.attack_id), None
            )
            if attack:
                if result.result.value == "FAIL":
                    self.failed_patterns.append(attack.prompt[:100])
                elif result.result.value == "PASS":
                    self.successful_patterns.append(attack.prompt[:100])

    def get_summary(self) -> dict[str, Any]:
        """Return a summary dict of the current context state."""
        from collections import Counter

        statuses = [r.result.value for r in self.validation_results]
        counts = Counter(statuses)
        return {
            "total_attacks": len(self.attack_results),
            "passed": counts.get("PASS", 0),
            "warnings": counts.get("WARNING", 0),
            "failed": counts.get("FAIL", 0),
            "token_usage": self.token_usage,
            "estimated_cost": sum(r.estimated_cost for r in self.attack_results),
            "selected_vectors": self.selected_vectors,
            "guardrail_strength": (
                self.recon_findings.guardrail_strength if self.recon_findings else "unknown"
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize the full context to a plain dictionary."""
        return {
            "recon_findings": self.recon_findings.model_dump() if self.recon_findings else None,
            "selected_vectors": self.selected_vectors,
            "attack_results": [r.model_dump() for r in self.attack_results],
            "validation_results": [r.model_dump() for r in self.validation_results],
            "successful_patterns": self.successful_patterns,
            "failed_patterns": self.failed_patterns,
            "token_usage": self.token_usage,
            "metadata": self.metadata,
        }
