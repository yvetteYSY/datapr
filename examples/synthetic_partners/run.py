#!/usr/bin/env python3
"""Run explicitly synthetic design-partner acceptance scenarios."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = Path(__file__).resolve().parent


def _command(*arguments: str) -> list[str]:
    return [sys.executable, "-m", "datapr.cli", *arguments]


def _run(
    arguments: list[str], expected_codes: frozenset[int] = frozenset({0})
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        arguments,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode not in expected_codes:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(
            f"command exited {result.returncode}: {' '.join(arguments)}\n{detail}"
        )
    return result


def _scenario_names() -> list[str]:
    return sorted(path.parent.name for path in SCENARIOS.glob("*/expected.json"))


def _analysis_args(scenario: Path) -> list[str]:
    arguments = [
        "--base-manifest",
        str(scenario / "base_manifest.json"),
        "--head-manifest",
        str(scenario / "head_manifest.json"),
        "--config",
        str(scenario / "datapr.yml"),
    ]
    base_data = scenario / "data" / "base"
    head_data = scenario / "data" / "head"
    if base_data.is_dir() or head_data.is_dir():
        arguments.extend(
            ["--base-data-dir", str(base_data), "--head-data-dir", str(head_data)]
        )
    return arguments


def run_scenario(name: str, output_root: Path) -> dict[str, Any]:
    scenario = SCENARIOS / name
    expected = json.loads((scenario / "expected.json").read_text(encoding="utf-8"))
    output = output_root / name
    output.mkdir(parents=True, exist_ok=True)

    for manifest in ("base_manifest.json", "head_manifest.json"):
        _run(_command("doctor", str(scenario / manifest)))

    analysis_args = _analysis_args(scenario)
    report_path = output / "report.json"
    expected_exit = (
        frozenset({1}) if expected["decision"] == "fail" else frozenset({0})
    )
    _run(
        _command(
            "compare",
            *analysis_args,
            "--format",
            "json",
            "--out",
            str(report_path),
            "--enforce",
        ),
        expected_codes=expected_exit,
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    finding_ids = {finding["id"] for finding in report["findings"]}
    missing = sorted(set(expected["required_findings"]) - finding_ids)
    if report["decision"] != expected["decision"]:
        raise AssertionError(
            f"{name}: expected {expected['decision']}, got {report['decision']}"
        )
    if missing:
        raise AssertionError(f"{name}: missing findings: {', '.join(missing)}")

    measurement_path = output / "measurement.json"
    _run(
        _command(
            "measure",
            *analysis_args,
            "--out",
            str(measurement_path),
        )
    )
    measurement_text = measurement_path.read_text(encoding="utf-8")
    measurement = json.loads(measurement_text)
    leaked = [
        marker for marker in expected["privacy_markers"] if marker in measurement_text
    ]
    if leaked:
        raise AssertionError(f"{name}: measurement leaked model markers: {leaked}")
    if measurement["decision"] != expected["decision"]:
        raise AssertionError(f"{name}: compare and measure decisions differ")

    return {
        "prototype": name,
        "adapter": expected["adapter"],
        "decision": report["decision"],
        "findings": len(report["findings"]),
        "coverage_complete": measurement["coverage"]["complete"],
        "differential_execution": measurement["coverage"][
            "differential_execution"
        ],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--partner",
        action="append",
        choices=_scenario_names(),
        help="run one prototype; repeat to run more than one",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        help="retain generated reports in this directory",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    names = args.partner or _scenario_names()
    if args.out_dir:
        output_root = args.out_dir.resolve()
        output_root.mkdir(parents=True, exist_ok=True)
        summaries = [run_scenario(name, output_root) for name in names]
    else:
        with tempfile.TemporaryDirectory(prefix="datapr-synthetic-") as directory:
            summaries = [run_scenario(name, Path(directory)) for name in names]
    print(json.dumps({"synthetic": True, "prototypes": summaries}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
