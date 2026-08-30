"""Command-line interface for DataPR."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from datapr import __version__
from datapr.analyzer import compare
from datapr.config import ConfigError, load_config
from datapr.manifest import ManifestError, load_manifest
from datapr.policy import apply_policy
from datapr.render import render_json, render_markdown, render_text


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="datapr", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    doctor = commands.add_parser("doctor", help="validate a dbt manifest")
    doctor.add_argument("manifest")

    comparison = commands.add_parser("compare", help="compare two dbt manifests")
    comparison.add_argument("--base-manifest", required=True)
    comparison.add_argument("--head-manifest", required=True)
    comparison.add_argument("--config", help="path to datapr.yml")
    comparison.add_argument(
        "--format", choices=("text", "json", "markdown"), default="text"
    )
    comparison.add_argument("--out", help="write the report to a file")
    comparison.add_argument(
        "--enforce", action="store_true", help="exit 1 when policy decides fail"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "doctor":
            manifest = load_manifest(args.manifest)
            print(f"OK: {manifest.path} contains {len(manifest.models)} dbt models")
            return 0

        config = load_config(args.config)
        result = apply_policy(compare(
            load_manifest(args.base_manifest), load_manifest(args.head_manifest)
        ), config.policy)
        if args.format == "json":
            output = render_json(result)
        elif args.format == "markdown":
            output = render_markdown(result)
        else:
            output = render_text(result)
        if args.out:
            Path(args.out).write_text(output + "\n", encoding="utf-8")
        else:
            print(output)
        return 1 if args.enforce and result.decision == "fail" else 0
    except (ConfigError, ManifestError) as exc:
        print(f"datapr: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
