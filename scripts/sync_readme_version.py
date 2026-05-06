"""Sync README version displays from pyproject.toml."""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = ROOT / "pyproject.toml"
README_PATH = ROOT / "README.md"

STATUS_BADGE_RE = re.compile(
    r"!\[Status\]\(https://img\.shields\.io/badge/Status-v(?P<version>[^-]+)-orange\)"
)


def read_project_version() -> str:
    """Return the package version from pyproject.toml."""
    with PYPROJECT_PATH.open("rb") as file:
        data = tomllib.load(file)
    return str(data["project"]["version"])


def synced_readme_content(content: str, version: str) -> str:
    """Return README content with the status badge version replaced."""
    replacement = f"![Status](https://img.shields.io/badge/Status-v{version}-orange)"
    updated, count = STATUS_BADGE_RE.subn(replacement, content)
    if count != 1:
        raise RuntimeError("Expected exactly one README status badge to sync")
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if README.md is not already synced",
    )
    args = parser.parse_args()

    version = read_project_version()
    content = README_PATH.read_text(encoding="utf-8")
    updated = synced_readme_content(content, version)

    if args.check:
        if content != updated:
            print(f"README.md status badge is not synced to version {version}", file=sys.stderr)
            return 1
        return 0

    if content != updated:
        README_PATH.write_text(updated, encoding="utf-8")
        print(f"Synced README.md status badge to v{version}")
    else:
        print(f"README.md status badge already synced to v{version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
