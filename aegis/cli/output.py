"""Rich output helpers for Aegis AI CLI."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aegis.cli.banner import BANNER
from aegis.core.models import SessionSummary, ValidationStatus

# Shared console instance used across all CLI output
console = Console()


def print_banner() -> None:
    """Print the Aegis AI ASCII banner."""
    console.print(BANNER, justify="center")


def print_phase(name: str, status: str) -> None:
    """Print a colored phase progress indicator.

    Args:
        name: Phase name (e.g. "Recon", "Execute").
        status: Phase status - "running", "done", "error".
    """
    status_styles = {
        "running": "[bold yellow]RUNNING[/bold yellow]",
        "done": "[bold green]DONE[/bold green]",
        "error": "[bold red]ERROR[/bold red]",
        "skipped": "[dim]SKIPPED[/dim]",
    }
    styled_status = status_styles.get(status.lower(), f"[white]{status.upper()}[/white]")
    console.print(f"  [dim]>>>[/dim] [bold]{name:<20}[/bold] {styled_status}")


def print_result(attack_id: str, result: str) -> None:
    """Print a colored PASS/WARN/FAIL result line.

    Args:
        attack_id: Short ID or name to display.
        result: "PASS", "WARNING", or "FAIL".
    """
    style_map = {
        ValidationStatus.PASS.value: "[bold green]PASS[/bold green]",
        ValidationStatus.WARNING.value: "[bold yellow]WARN[/bold yellow]",
        ValidationStatus.FAIL.value: "[bold red]FAIL[/bold red]",
    }
    styled = style_map.get(result, f"[white]{result}[/white]")
    console.print(f"  [{attack_id[:36]:<36}] {styled}")


def print_summary(session_summary: SessionSummary) -> None:
    """Print a Rich table with session summary statistics.

    Args:
        session_summary: The SessionSummary Pydantic model.
    """
    table = Table(title="Session Summary", border_style="cyan", show_header=True)
    table.add_column("Field", style="dim", width=22)
    table.add_column("Value", style="bold")

    duration = ""
    if session_summary.started_at and session_summary.finished_at:
        secs = (session_summary.finished_at - session_summary.started_at).total_seconds()
        duration = f"{secs:.1f}s"

    risk_style = _risk_style(session_summary.overall_risk_score)

    table.add_row("Session ID", session_summary.session_id[:16] + "...")
    table.add_row("Target", session_summary.target_url)
    table.add_row("Provider / Model", f"{session_summary.provider} / {session_summary.model}")
    table.add_row("Status", session_summary.status.upper())
    table.add_row("Duration", duration or "N/A")
    table.add_row("Total Attacks", str(session_summary.total_attacks))
    table.add_row("Passed", f"[green]{session_summary.passed}[/green]")
    table.add_row("Warnings", f"[yellow]{session_summary.warnings}[/yellow]")
    table.add_row("Failed", f"[red]{session_summary.failed}[/red]")
    table.add_row("Total Tokens", str(session_summary.total_tokens))
    table.add_row("Est. Cost", f"${session_summary.estimated_cost:.4f}")
    table.add_row(
        "Risk Score",
        f"{risk_style}{session_summary.overall_risk_score:.1f}/100[/]",
    )

    console.print(table)


def print_error(msg: str) -> None:
    """Print a red error message panel.

    Args:
        msg: The error message to display.
    """
    console.print(Panel(Text(msg, style="bold red"), title="[red]Error[/red]", border_style="red"))


def _risk_style(score: float) -> str:
    """Return Rich color markup for a risk score."""
    if score >= 90:
        return "[bold red]"
    elif score >= 71:
        return "[red]"
    elif score >= 31:
        return "[yellow]"
    return "[green]"
