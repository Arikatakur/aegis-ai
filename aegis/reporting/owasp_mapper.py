"""OWASP LLM Top 10 mapper for Aegis AI findings."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypedDict

from aegis.core.models import ValidationResult


class OWASPSummary(TypedDict):
    """Aggregated counts for one OWASP category."""

    name: str
    failures: int
    warnings: int
    passes: int


# OWASP LLM Top 10 definitions
OWASP_CATEGORIES: dict[str, dict[str, str]] = {
    "LLM01": {
        "name": "Prompt Injection",
        "description": (
            "User-supplied prompts manipulate the LLM to ignore instructions "
            "or override intended behaviour."
        ),
        "url": "https://owasp.org/www-project-top-10-for-large-language-model-applications/",
    },
    "LLM02": {
        "name": "Sensitive Information Disclosure",
        "description": ("The LLM reveals sensitive or confidential information it should not."),
        "url": "https://owasp.org/www-project-top-10-for-large-language-model-applications/",
    },
    "LLM04": {
        "name": "Data and Model Poisoning",
        "description": (
            "Malicious data injected into training or retrieval context manipulates "
            "model behaviour."
        ),
        "url": "https://owasp.org/www-project-top-10-for-large-language-model-applications/",
    },
    "LLM07": {
        "name": "System Prompt Leakage",
        "description": ("The system prompt or hidden instructions are exposed to the user."),
        "url": "https://owasp.org/www-project-top-10-for-large-language-model-applications/",
    },
    "LLM10": {
        "name": "Unbounded Consumption",
        "description": ("Excessive token usage leading to denial-of-service or unexpected costs."),
        "url": "https://owasp.org/www-project-top-10-for-large-language-model-applications/",
    },
}

# Attack category to OWASP mapping
_CATEGORY_OWASP_MAP: dict[str, list[str]] = {
    "jailbreak": ["LLM01"],
    "prompt_injection": ["LLM01"],
    "data_exfiltration": ["LLM02", "LLM07"],
    "encoding": ["LLM01"],
    "context_poisoning": ["LLM04"],
    "recon": [],
}


class OWASPMapper:
    """Maps attack categories and findings to OWASP LLM Top 10 categories."""

    def map_category(self, category: str) -> list[str]:
        """Return OWASP IDs for a given attack category.

        Args:
            category: Attack category name.

        Returns:
            List of OWASP LLM Top 10 IDs.
        """
        return _CATEGORY_OWASP_MAP.get(category.lower(), ["LLM01"])

    def get_category_info(self, owasp_id: str) -> dict[str, str]:
        """Return name and description for an OWASP ID.

        Args:
            owasp_id: OWASP LLM category ID (e.g. "LLM01").

        Returns:
            Dict with name and description keys.
        """
        return OWASP_CATEGORIES.get(owasp_id, {"name": owasp_id, "description": ""})

    def summarise_findings(
        self, validation_results: Sequence[ValidationResult]
    ) -> dict[str, OWASPSummary]:
        """Aggregate validation results by OWASP category.

        Args:
            validation_results: List of ValidationResult objects.

        Returns:
            Dict keyed by OWASP ID with counts and details.
        """
        summary: dict[str, OWASPSummary] = {}
        for vr in validation_results:
            for owasp_id in vr.owasp_mappings:
                if owasp_id not in summary:
                    info = self.get_category_info(owasp_id)
                    summary[owasp_id] = {
                        "name": info.get("name", owasp_id),
                        "failures": 0,
                        "warnings": 0,
                        "passes": 0,
                    }
                status = vr.result.value
                if status == "FAIL":
                    summary[owasp_id]["failures"] += 1
                elif status == "WARNING":
                    summary[owasp_id]["warnings"] += 1
                else:
                    summary[owasp_id]["passes"] += 1

        return summary
