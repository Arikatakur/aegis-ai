"""Report export functions for Aegis AI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aegis import __version__


def export_json(report_data: dict[str, Any], path: Path) -> None:
    """Export report as JSON.

    Args:
        report_data: Report dictionary to serialise.
        path: Output file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report_data, indent=2, default=str),
        encoding="utf-8",
    )


def export_txt(report_data: dict[str, Any], path: Path) -> None:
    """Export report as plain text.

    Args:
        report_data: Report dictionary.
        path: Output file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []

    meta = report_data.get("meta", {})
    lines.append("=" * 70)
    lines.append("AEGIS AI RED-TEAM REPORT")
    lines.append(f"Generated: {meta.get('generated_at', 'N/A')}")
    lines.append(f"Session:   {meta.get('session_id', 'N/A')}")
    lines.append("=" * 70)
    lines.append("")

    target = report_data.get("target", {})
    lines.append("TARGET")
    lines.append(f"  Endpoint: {target.get('endpoint', 'N/A')}")
    lines.append(f"  Provider: {target.get('provider', 'N/A')}")
    lines.append(f"  Model:    {target.get('model', 'N/A')}")
    lines.append("")

    risk = report_data.get("risk", {})
    lines.append("RISK ASSESSMENT")
    lines.append(f"  Score: {risk.get('score', 0):.1f}/100")
    lines.append(f"  Level: {risk.get('level', 'Unknown')}")
    lines.append(f"  {risk.get('description', '')}")
    lines.append("")

    stats = report_data.get("statistics", {})
    lines.append("STATISTICS")
    lines.append(f"  Total Attacks: {stats.get('total_attacks', 0)}")
    lines.append(f"  Passed:        {stats.get('passed', 0)}")
    lines.append(f"  Warnings:      {stats.get('warnings', 0)}")
    lines.append(f"  Failed:        {stats.get('failed', 0)}")
    lines.append(f"  Total Tokens:  {report_data.get('token_usage', {}).get('total_tokens', 0)}")
    lines.append(f"  Est. Cost:     ${report_data.get('estimated_cost', 0):.4f}")
    lines.append("")

    lines.append("EXECUTIVE SUMMARY")
    lines.append(report_data.get("executive_summary", ""))
    lines.append("")

    lines.append("OWASP FINDINGS")
    for owasp_id, info in report_data.get("owasp_mapping", {}).items():
        lines.append(
            f"  {owasp_id} {info.get('name', '')}: "
            f"{info.get('failures', 0)} failures, {info.get('warnings', 0)} warnings"
        )
    lines.append("")

    lines.append("FINDINGS")
    for f in report_data.get("findings", []):
        lines.append(f"  [{f.get('validation_status', '?')}] {f.get('attack_id', '')}")
        lines.append(f"    Category: {f.get('category', '')}")
        lines.append(f"    Evidence: {f.get('evidence', '')}")
        lines.append(f"    Prompt:   {f.get('prompt', '')[:120]}")
        lines.append(f"    Response: {f.get('response', '')[:120]}")
        lines.append("")

    lines.append("RECOMMENDATIONS")
    for rec in report_data.get("recommendations", []):
        lines.append(f"  - {rec}")
    lines.append("")
    lines.append("=" * 70)

    path.write_text("\n".join(lines), encoding="utf-8")


def export_markdown(report_data: dict[str, Any], path: Path) -> None:
    """Export report as Markdown using Jinja2 template if available, else plain.

    Args:
        report_data: Report dictionary.
        path: Output file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    template_path = Path(__file__).parent / "templates" / "markdown_report.j2"
    if template_path.exists():
        try:
            from jinja2 import Environment, FileSystemLoader

            env = Environment(
                loader=FileSystemLoader(str(template_path.parent)),
                autoescape=False,
            )
            template = env.get_template("markdown_report.j2")
            content = template.render(**report_data)
            path.write_text(content, encoding="utf-8")
            return
        except Exception:
            pass  # Fall through to plain markdown

    # Fallback: plain markdown without Jinja2
    _export_markdown_plain(report_data, path)


def _export_markdown_plain(report_data: dict[str, Any], path: Path) -> None:
    """Generate markdown report without Jinja2 template."""
    meta = report_data.get("meta", {})
    target = report_data.get("target", {})
    risk = report_data.get("risk", {})
    stats = report_data.get("statistics", {})

    lines: list[str] = [
        "# Aegis AI Red-Team Report",
        "",
        f"**Generated:** {meta.get('generated_at', 'N/A')}  ",
        f"**Session ID:** `{meta.get('session_id', 'N/A')}`",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        report_data.get("executive_summary", ""),
        "",
        "---",
        "",
        "## Risk Assessment",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Score | **{risk.get('score', 0):.1f} / 100** |",
        f"| Level | **{risk.get('level', 'Unknown')}** |",
        "",
        risk.get("description", ""),
        "",
        "---",
        "",
        "## Target",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Endpoint | `{target.get('endpoint', 'N/A')}` |",
        f"| Provider | {target.get('provider', 'N/A')} |",
        f"| Model | {target.get('model', 'N/A')} |",
        f"| Mode | {target.get('mode', 'N/A')} |",
        "",
        "---",
        "",
        "## Statistics",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Total Attacks | {stats.get('total_attacks', 0)} |",
        f"| Passed | {stats.get('passed', 0)} |",
        f"| Warnings | {stats.get('warnings', 0)} |",
        f"| Failed | {stats.get('failed', 0)} |",
        f"| Total Tokens | {report_data.get('token_usage', {}).get('total_tokens', 0)} |",
        f"| Est. Cost | ${report_data.get('estimated_cost', 0):.4f} |",
        "",
        "---",
        "",
        "## OWASP LLM Top 10 Mapping",
        "",
    ]

    owasp = report_data.get("owasp_mapping", {})
    if owasp:
        lines += ["| ID | Category | Failures | Warnings | Passes |", "|---|---|---|---|---|"]
        for owasp_id, info in owasp.items():
            lines.append(
                f"| {owasp_id} | {info.get('name', '')} | "
                f"{info.get('failures', 0)} | {info.get('warnings', 0)} | "
                f"{info.get('passes', 0)} |"
            )
    else:
        lines.append("_No OWASP findings recorded._")

    lines += [
        "",
        "---",
        "",
        "## Findings",
        "",
    ]

    for f in report_data.get("findings", []):
        status = f.get("validation_status", "UNKNOWN")
        emoji = {"FAIL": "🔴", "WARNING": "🟡", "PASS": "🟢"}.get(status, "⚪")
        lines += [
            f"### {emoji} [{status}] `{f.get('attack_id', '')}`",
            "",
            f"**Category:** {f.get('category', '')}  ",
            f"**Agent:** {f.get('agent', '')}  ",
            f"**Confidence:** {f.get('confidence', 0):.0%}  ",
            f"**OWASP:** {', '.join(f.get('owasp', [])) or 'N/A'}",
            "",
            "**Prompt:**",
            f"```\n{f.get('prompt', '')}\n```",
            "",
            "**Response:**",
            f"```\n{f.get('response', '')[:500]}\n```",
            "",
            f"**Evidence:** {f.get('evidence', 'None')}",
            "",
        ]

    lines += [
        "---",
        "",
        "## Recommendations",
        "",
    ]
    for rec in report_data.get("recommendations", []):
        lines.append(f"- {rec}")

    lines += [
        "",
        "---",
        "",
        f"_Report generated by [Aegis AI](https://github.com/aegis-ai) v{__version__}_",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")


def export_html(report_data: dict[str, Any], path: Path) -> None:
    """Export report as HTML using Jinja2 template.

    Args:
        report_data: Report dictionary.
        path: Output file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    template_path = Path(__file__).parent / "templates" / "html_report.j2"
    if not template_path.exists():
        path.write_text("<html><body><p>HTML template not found.</p></body></html>")
        return

    from jinja2 import Environment, FileSystemLoader

    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=True,
    )
    template = env.get_template("html_report.j2")
    content = template.render(**report_data)
    path.write_text(content, encoding="utf-8")
