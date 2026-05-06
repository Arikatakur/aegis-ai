"""ASCII banner for Aegis AI CLI."""

from aegis import __version__

BANNER = (
    rf"""
[bold red]
    █████╗ ███████╗ ██████╗ ██╗███████╗
   ██╔══██╗██╔════╝██╔════╝ ██║██╔════╝
   ███████║█████╗  ██║  ███╗██║███████╗
   ██╔══██║██╔══╝  ██║   ██║██║╚════██║
   ██║  ██║███████╗╚██████╔╝██║███████║
   ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝╚══════╝
[/bold red]

[bold white]      Autonomous LLM Red-Teaming Platform[/bold white]
[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]
"""
    f"[bold red]      v{__version__}[/bold red] [dim]|[/dim] "
    "[cyan]Local-first[/cyan] [dim]|[/dim] "
    "[magenta]OWASP-mapped[/magenta]\n"
)

BANNER_SHORT = (
    f"[bold red]AEGIS AI[/bold red] "
    f"[dim]v{__version__} | Autonomous LLM Red-Teaming Platform[/dim]"
)
