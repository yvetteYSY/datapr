#!/usr/bin/env python3
"""Verify that a DataPR source tree is internally consistent for release."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[a-z]+[0-9]+)?$")


def _match(path: Path, pattern: str, description: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        raise ValueError(f"cannot find {description} in {path.relative_to(ROOT)}")
    return match.group(1)


def project_version() -> str:
    return _match(
        ROOT / "pyproject.toml",
        r'^version = "([^"]+)"$',
        "project version",
    )


def verify_release(tag: str | None = None) -> list[str]:
    errors: list[str] = []
    version = project_version()
    package_version = _match(
        ROOT / "src/datapr/__init__.py",
        r'^__version__ = "([^"]+)"$',
        "package version",
    )
    if not VERSION_PATTERN.fullmatch(version):
        errors.append(f"project version is not supported SemVer/PEP 440: {version}")
    if package_version != version:
        errors.append(
            f"package version {package_version} does not match project version {version}"
        )
    if tag is not None and tag != f"v{version}":
        errors.append(f"tag {tag} does not match project version v{version}")

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"## [{version}]" not in changelog:
        errors.append(f"CHANGELOG.md has no {version} release section")
    notes = ROOT / "docs/releases" / f"v{version}.md"
    if not notes.is_file():
        errors.append(f"missing release notes: docs/releases/v{version}.md")
    elif f"# DataPR v{version}" not in notes.read_text(encoding="utf-8"):
        errors.append(f"release notes do not declare DataPR v{version}")

    for schema in sorted((ROOT / "schemas").glob("*.schema.json")):
        try:
            json.loads(schema.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid schema JSON in {schema.relative_to(ROOT)}: {exc}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="require this release tag to match the version")
    args = parser.parse_args(argv)
    try:
        errors = verify_release(args.tag)
    except (OSError, ValueError) as exc:
        print(f"release verification failed: {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"release verification failed: {error}", file=sys.stderr)
        return 1
    print(f"release verification passed for v{project_version()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
