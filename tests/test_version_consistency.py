"""Version consistency checks."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import aegis

ROOT = Path(__file__).resolve().parents[1]


def _pyproject_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as file:
        data = tomllib.load(file)
    return str(data["project"]["version"])


def test_package_version_matches_pyproject() -> None:
    assert aegis.__version__ == _pyproject_version()


def test_readme_status_badge_matches_pyproject() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(
        r"!\[Status\]\(https://img\.shields\.io/badge/Status-v(?P<version>[^-]+)-orange\)",
        readme,
    )
    assert match is not None
    assert match.group("version") == _pyproject_version()
