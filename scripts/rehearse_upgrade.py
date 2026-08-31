#!/usr/bin/env python3
"""Rehearse upgrade to a candidate wheel and rollback to v0.5.0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import venv

from verify_release import project_version


ROOT = Path(__file__).resolve().parents[1]
BASELINE_VERSION = "0.5.0"
BASELINE_WHEEL = (
    "https://github.com/yvetteYSY/datapr/releases/download/"
    "v0.5.0/datapr-0.5.0-py3-none-any.whl"
    "#sha256=5b03b2a8b8a32fa8de32861d68f2965e87bb68451abe958b8ba5e1fbcc0c1016"
)


def _run(arguments: list[str], *, cwd: Path = ROOT) -> str:
    result = subprocess.run(
        arguments,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(
            f"command exited {result.returncode}: {' '.join(arguments)}\n{detail}"
        )
    return result.stdout.strip()


def _report(datapr: Path, destination: Path) -> dict[str, object]:
    _run(
        [
            str(datapr),
            "compare",
            "--base-manifest",
            "tests/fixtures/base_manifest.json",
            "--head-manifest",
            "tests/fixtures/head_manifest.json",
            "--format",
            "json",
            "--out",
            str(destination),
        ]
    )
    return json.loads(destination.read_text(encoding="utf-8"))


def rehearse(candidate_wheel: Path) -> dict[str, object]:
    candidate_wheel = candidate_wheel.resolve()
    if not candidate_wheel.is_file():
        raise ValueError(f"candidate wheel not found: {candidate_wheel}")

    with tempfile.TemporaryDirectory(prefix="datapr-upgrade-") as directory:
        rehearsal = Path(directory)
        environment = rehearsal / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        binary = environment / "bin"
        python = binary / "python"
        datapr = binary / "datapr"

        _run([str(python), "-m", "pip", "install", "--quiet", BASELINE_WHEEL])
        baseline_version = _run([str(datapr), "--version"])
        baseline = _report(datapr, rehearsal / "baseline.json")

        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--quiet",
                "--force-reinstall",
                str(candidate_wheel),
            ]
        )
        candidate_version = _run([str(datapr), "--version"])
        candidate = _report(datapr, rehearsal / "candidate.json")
        if candidate != baseline:
            raise AssertionError("candidate changed the v0.5 comparison contract")

        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--quiet",
                "--force-reinstall",
                BASELINE_WHEEL,
            ]
        )
        rollback_version = _run([str(datapr), "--version"])
        rollback = _report(datapr, rehearsal / "rollback.json")
        if rollback != baseline:
            raise AssertionError("rollback did not restore the v0.5 comparison contract")

    expected_candidate = project_version()
    if baseline_version != BASELINE_VERSION:
        raise AssertionError(
            f"expected baseline {BASELINE_VERSION}, got {baseline_version}"
        )
    if candidate_version != expected_candidate:
        raise AssertionError(
            f"expected candidate {expected_candidate}, got {candidate_version}"
        )
    if rollback_version != BASELINE_VERSION:
        raise AssertionError(
            f"expected rollback {BASELINE_VERSION}, got {rollback_version}"
        )
    return {
        "baseline": baseline_version,
        "candidate": candidate_version,
        "rollback": rollback_version,
        "comparison_contract_equal": True,
        "decision": candidate["decision"],
        "findings": len(candidate["findings"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-wheel", required=True, type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(rehearse(args.candidate_wheel), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
