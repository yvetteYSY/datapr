"""Command-line interface for DataPR."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from time import perf_counter

from datapr import __version__
from datapr.analyzer import compare
from datapr.config import ConfigError, load_config
from datapr.git import GitError, manifests_from_range
from datapr.lineage import add_column_lineage, add_sql_risk_findings
from datapr.manifest import ManifestError, load_manifest
from datapr.measurement import render_measurement
from datapr.models import Comparison
from datapr.policy import apply_policy
from datapr.profiler import ProfileError, add_profile_findings
from datapr.renames import add_rename_candidates
from datapr.render import render_json, render_markdown, render_text


def _add_analysis_arguments(command: argparse.ArgumentParser) -> None:
    command.add_argument(
        "revision_range", nargs="?", help="Git range such as main..HEAD"
    )
    command.add_argument("--base-manifest")
    command.add_argument("--head-manifest")
    command.add_argument(
        "--manifest-path",
        default="target/manifest.json",
        help="artifact path within each Git revision",
    )
    command.add_argument("--repo", default=".", help="Git repository directory")
    command.add_argument("--config", help="path to datapr.yml")
    command.add_argument("--base-data-dir")
    command.add_argument("--head-data-dir")
    command.add_argument("--out", help="write output to a file")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="datapr", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    doctor = commands.add_parser("doctor", help="validate a dbt manifest")
    doctor.add_argument("manifest")

    comparison = commands.add_parser("compare", help="compare two dbt manifests")
    _add_analysis_arguments(comparison)
    comparison.add_argument(
        "--format", choices=("text", "json", "markdown"), default="text"
    )
    comparison.add_argument(
        "--enforce", action="store_true", help="exit 1 when policy decides fail"
    )

    measurement = commands.add_parser(
        "measure", help="emit a privacy-safe adoption measurement"
    )
    _add_analysis_arguments(measurement)
    return parser


def _analyze(args: argparse.Namespace) -> Comparison:
    config = load_config(args.config)
    if args.revision_range:
        if args.base_manifest or args.head_manifest:
            raise GitError("use a revision range or explicit manifest paths, not both")
        base, head = manifests_from_range(
            args.revision_range, args.manifest_path, args.repo
        )
    elif args.base_manifest and args.head_manifest:
        base, head = load_manifest(args.base_manifest), load_manifest(
            args.head_manifest
        )
    else:
        raise GitError("provide BASE..HEAD or both --base-manifest and --head-manifest")
    execution = config.execution
    if args.base_data_dir or args.head_data_dir:
        from dataclasses import replace

        execution = replace(
            execution,
            base_data_dir=args.base_data_dir or execution.base_data_dir,
            head_data_dir=args.head_data_dir or execution.head_data_dir,
        )
    result = compare(base, head)
    result = add_sql_risk_findings(result, base, head)
    result = add_rename_candidates(result, base, head)
    result = add_column_lineage(result, head)
    result = add_profile_findings(result, execution, config.policy)
    return apply_policy(result, config.policy)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "doctor":
            manifest = load_manifest(args.manifest)
            print(f"OK: {manifest.path} contains {len(manifest.models)} dbt models")
            return 0

        started = perf_counter()
        result = _analyze(args)
        analysis_seconds = perf_counter() - started
        if args.command == "measure":
            output = render_measurement(result, analysis_seconds)
        elif args.format == "json":
            output = render_json(result)
        elif args.format == "markdown":
            output = render_markdown(result)
        else:
            output = render_text(result)
        if args.out:
            Path(args.out).write_text(output + "\n", encoding="utf-8")
        else:
            print(output)
        return (
            1
            if args.command == "compare" and args.enforce and result.decision == "fail"
            else 0
        )
    except (ConfigError, GitError, ManifestError, ProfileError) as exc:
        print(f"datapr: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
