"""Command-line interface for DataPR."""

from __future__ import annotations

import argparse
import json
import sys

from datapr import __version__
from datapr.analyzer import Comparison, compare
from datapr.manifest import ManifestError, load_manifest


def _render_text(result: Comparison) -> str:
    lines = [
        f"DataPR compared {result.models_base} base models with {result.models_head} head models.",
        f"Changed models: {len(result.changes)}",
    ]
    for change in result.changes:
        lines.append(f"\n{change.name}  {change.kind.upper()}")
        if change.downstream:
            lines.append(
                f"  downstream ({len(change.downstream)}): {', '.join(change.downstream)}"
            )
        for column in change.columns:
            detail = column.kind
            if column.before != column.after:
                detail += f" ({column.before or '-'} -> {column.after or '-'})"
            lines.append(f"  column {column.column}: {detail}")
    return "\n".join(lines)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="datapr", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    doctor = commands.add_parser("doctor", help="validate a dbt manifest")
    doctor.add_argument("manifest")

    comparison = commands.add_parser("compare", help="compare two dbt manifests")
    comparison.add_argument("--base-manifest", required=True)
    comparison.add_argument("--head-manifest", required=True)
    comparison.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "doctor":
            manifest = load_manifest(args.manifest)
            print(f"OK: {manifest.path} contains {len(manifest.models)} dbt models")
            return 0

        result = compare(
            load_manifest(args.base_manifest), load_manifest(args.head_manifest)
        )
        if args.format == "json":
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(_render_text(result))
        return 0
    except ManifestError as exc:
        print(f"datapr: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
