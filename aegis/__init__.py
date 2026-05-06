"""Aegis AI - Autonomous local-first LLM red-teaming platform."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("aegis-ai")
except PackageNotFoundError:
    __version__ = "0.1.0"

__author__ = "Aegis AI"
