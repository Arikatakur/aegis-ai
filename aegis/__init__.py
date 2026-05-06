"""Aegis AI - Autonomous local-first LLM red-teaming platform."""

import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def _version_from_pyproject() -> str:
    """Read the source-tree version when package metadata is unavailable."""
    for parent in Path(__file__).resolve().parents:
        pyproject_path = parent / "pyproject.toml"
        if pyproject_path.exists():
            with pyproject_path.open("rb") as file:
                data = tomllib.load(file)
            return str(data["project"]["version"])
    return "0+unknown"


try:
    __version__ = version("aegis-ai")
except PackageNotFoundError:
    __version__ = _version_from_pyproject()

__author__ = "Aegis AI"
