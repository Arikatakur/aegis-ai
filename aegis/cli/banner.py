"""ASCII banner for Aegis AI CLI."""

from aegis import __version__

BANNER = rf"""
    _          _  ___   ___
   /_\   ___  (_)/ __| |_ _|
  / _ \ / -_) | |\__ \  | |
 /_/ \_\\___|_|_||___/ |___|

 Autonomous LLM Red-Teaming Platform
 ────────────────────────────────────────
 v{__version__}  |  Local-first  |  OWASP-mapped
"""

BANNER_SHORT = (
    f"[bold cyan]Aegis AI[/bold cyan] [dim]v{__version__} | Autonomous LLM Red-Teaming[/dim]"
)
