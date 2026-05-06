"""Aegis AI Typer CLI application."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.prompt import Confirm, Prompt

from aegis.cli.output import console, print_banner, print_error, print_phase, print_summary
from aegis.config.target_config import TargetConfig
from aegis.core.models import SessionSummary

app = typer.Typer(
    name="aegis",
    help="Aegis AI - Autonomous LLM Red-Teaming Platform",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@app.command("init")
def init_command() -> None:
    """[bold]Initialize[/bold] Aegis AI configuration interactively."""
    print_banner()
    console.print("[bold cyan]Aegis AI - Interactive Configuration[/bold cyan]\n")

    endpoint = Prompt.ask("Target endpoint", default="http://localhost:9000/chat")
    provider = Prompt.ask("Provider", default="openai")
    model = Prompt.ask("Model", default="gpt-4o-mini")
    api_key = Prompt.ask("API key", password=True, default="")
    mode = Prompt.ask("Run mode", choices=["quick", "standard", "deep"], default="standard")

    config_data = {
        "endpoint": endpoint,
        "provider": provider,
        "model": model,
        "api_key": api_key,
        "timeout": 30,
        "concurrency": 5,
        "mode": mode,
        "system_prompt": "You are a helpful assistant.",
    }

    config_path = Path("target.json")
    config_path.write_text(json.dumps(config_data, indent=2))
    console.print(f"\n[green]Config saved to {config_path}[/green]")
    console.print("[dim]Run [bold]aegis validate-config[/bold] to verify.[/dim]")


@app.command("run")
def run_command(
    target: Optional[str] = typer.Option(None, "--target", "-t", help="Target endpoint URL"),
    mode: str = typer.Option("standard", "--mode", "-m", help="Run mode: quick, standard, deep"),
    concurrency: int = typer.Option(5, "--concurrency", "-c", help="Max concurrent requests"),
    categories: Optional[str] = typer.Option(
        None, "--categories", help="Comma-separated attack categories"
    ),
    format: str = typer.Option("markdown", "--format", "-f", help="Report format: markdown, json, txt"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory"),
    config_file: Optional[str] = typer.Option(
        None, "--config", help="Path to target config JSON"
    ),
) -> None:
    """[bold]Run[/bold] a full red-team assessment against the target LLM."""
    print_banner()
    console.print(f"[bold]Mode:[/bold] {mode} | [bold]Concurrency:[/bold] {concurrency}\n")

    # Load config
    try:
        target_config = _load_target_config(target, concurrency, mode, config_file)
    except Exception as exc:
        print_error(f"Config error: {exc}")
        raise typer.Exit(1) from exc

    console.print(f"[dim]Target:[/dim] {target_config.endpoint}")
    console.print(f"[dim]Model:[/dim]  {target_config.provider}/{target_config.model}\n")

    # Run via service runner
    from aegis.services.runner import Runner

    runner = Runner(reports_dir=output or "reports")

    async def _run() -> SessionSummary:
        return await runner.run(target_config=target_config, mode=mode)

    print_phase("Recon", "running")
    try:
        summary = asyncio.run(_run())
    except Exception as exc:
        print_error(f"Run failed: {exc}")
        raise typer.Exit(1) from exc

    print_summary(summary)
    console.print(f"\n[green]Report saved to reports/{summary.session_id}/[/green]")


@app.command("report")
def report_command(
    session: str = typer.Option(..., "--session", "-s", help="Session ID"),
    format: str = typer.Option("markdown", "--format", "-f", help="Report format"),
) -> None:
    """[bold]Generate[/bold] or re-export a report for a previous session."""
    print_banner()
    console.print(f"[dim]Re-generating report for session:[/dim] {session}")

    report_path = Path("reports") / session
    if not report_path.exists():
        print_error(f"Session directory not found: {report_path}")
        raise typer.Exit(1)

    json_file = report_path / "report.json"
    if not json_file.exists():
        print_error("No report.json found for this session. Run the session first.")
        raise typer.Exit(1)

    report_data = json.loads(json_file.read_text())

    from aegis.reporting.export import export_json, export_markdown, export_txt

    if format == "json":
        export_json(report_data, report_path / "report.json")
    elif format == "txt":
        export_txt(report_data, report_path / "report.txt")
    else:
        export_markdown(report_data, report_path / "report.md")

    console.print(f"[green]Report written to {report_path}/report.{format}[/green]")


@app.command("replay")
def replay_command(
    session: str = typer.Option(..., "--session", "-s", help="Session ID to replay"),
) -> None:
    """[bold]Replay[/bold] a previous session's attacks."""
    print_banner()
    console.print(f"[dim]Replaying session:[/dim] {session}")

    report_path = Path("reports") / session / "report.json"
    if not report_path.exists():
        print_error(f"Session report not found: {report_path}")
        raise typer.Exit(1)

    report_data = json.loads(report_path.read_text())
    findings = report_data.get("findings", [])
    console.print(f"[bold]{len(findings)} attack cases found.[/bold] Replaying...\n")

    # TODO: Re-execute attack cases from stored prompts
    console.print(
        "[yellow]Replay execution not yet implemented. "
        "Showing stored results instead.[/yellow]"
    )
    for f in findings:
        status = f.get("validation_status", "UNKNOWN")
        aid = f.get("attack_id", "?")[:12]
        console.print(f"  [{aid}] {status}")


@app.command("list-sessions")
def list_sessions_command() -> None:
    """[bold]List[/bold] all past sessions stored in the database."""
    print_banner()
    from aegis.db.database import get_session_factory
    from aegis.db.repositories import SessionRepository

    try:
        session_factory = get_session_factory()
        with session_factory() as db:
            repo = SessionRepository(db)
            sessions = repo.list_all()

        if not sessions:
            console.print("[dim]No sessions found.[/dim]")
            return

        from rich.table import Table

        table = Table(title="Past Sessions", border_style="cyan")
        table.add_column("Session ID", style="dim")
        table.add_column("Status")
        table.add_column("Target")
        table.add_column("Attacks")
        table.add_column("Risk")
        table.add_column("Started")

        for s in sessions:
            table.add_row(
                s.session_id[:16] + "...",
                s.status,
                s.target_url,
                str(s.total_attacks),
                f"{s.overall_risk_score:.1f}",
                str(s.started_at)[:19] if s.started_at else "N/A",
            )
        console.print(table)

    except Exception as exc:
        print_error(f"Could not list sessions: {exc}")


@app.command("mock-target")
def mock_target_command(
    port: int = typer.Option(9000, "--port", "-p", help="Port to listen on"),
    mode: str = typer.Option(
        "vulnerable", "--mode", "-m", help="Scenario mode: secure, vulnerable, random"
    ),
) -> None:
    """[bold]Start[/bold] a local mock LLM target for testing."""
    print_banner()
    import uvicorn

    from aegis.mock_target.app import create_app

    console.print(f"[bold green]Starting mock target on port {port} (mode: {mode})[/bold green]")
    console.print(f"[dim]Endpoint:[/dim] http://localhost:{port}/chat\n")

    mock_app = create_app(mode=mode)
    uvicorn.run(mock_app, host="0.0.0.0", port=port, log_level="warning")


@app.command("validate-config")
def validate_config_command(
    config_file: str = typer.Option("target.json", "--config", "-c", help="Config file path"),
) -> None:
    """[bold]Validate[/bold] target configuration file."""
    print_banner()
    config_path = Path(config_file)
    if not config_path.exists():
        print_error(f"Config file not found: {config_path}")
        raise typer.Exit(1)

    try:
        data = json.loads(config_path.read_text())
        cfg = TargetConfig(**data)
        console.print("[green]Config is valid.[/green]")
        console.print(f"  Endpoint:  {cfg.endpoint}")
        console.print(f"  Provider:  {cfg.provider}")
        console.print(f"  Model:     {cfg.model}")
        console.print(f"  API Key:   {cfg.masked_key}")
        console.print(f"  Mode:      {cfg.mode}")
    except Exception as exc:
        print_error(f"Invalid config: {exc}")
        raise typer.Exit(1) from exc


def _load_target_config(
    target: Optional[str],
    concurrency: int,
    mode: str,
    config_file: Optional[str],
) -> TargetConfig:
    """Load TargetConfig from file, env, or CLI flags."""
    from aegis.config import get_settings

    # Try config file
    if config_file and Path(config_file).exists():
        data = json.loads(Path(config_file).read_text())
        return TargetConfig(**data)

    # Try default target.json
    if Path("target.json").exists():
        data = json.loads(Path("target.json").read_text())
        return TargetConfig(**data)

    # Fall back to settings
    settings = get_settings()
    return TargetConfig(
        endpoint=target or settings.target_endpoint,
        provider=settings.target_provider,
        model=settings.target_model,
        api_key=settings.target_api_key,
        timeout=settings.request_timeout,
        concurrency=concurrency,
        mode=mode,
    )
