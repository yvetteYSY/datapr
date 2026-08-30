"""Benchmark the static DataPR pipeline on synthetic dbt-style manifests."""

from __future__ import annotations

import argparse
import gc
import math
import platform
import statistics
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import sqlglot

from datapr.analyzer import compare
from datapr.lineage import add_column_lineage, add_sql_risk_findings
from datapr.manifest import Manifest, Model
from datapr.renames import add_rename_candidates


@dataclass(frozen=True)
class BenchmarkResult:
    models: int
    changed_models: int
    iterations: int
    median_seconds: float
    p95_seconds: float
    minimum_seconds: float


def _manifest_pair(size: int) -> tuple[Manifest, Manifest]:
    if size <= 0:
        raise ValueError("benchmark size must be positive")
    base_models: dict[str, Model] = {}
    head_models: dict[str, Model] = {}
    change_interval = 100
    for index in range(size):
        unique_id = f"model.benchmark.model_{index:05d}"
        dependency = (
            frozenset({f"model.benchmark.model_{index - 1:05d}"})
            if index
            else frozenset()
        )
        sql = f"select {index}::integer as id"
        base_models[unique_id] = Model(
            unique_id=unique_id,
            name=f"model_{index:05d}",
            columns={"id": "integer"},
            dependencies=dependency,
            fingerprint=f"base-{index}",
            sql=sql,
        )
        changed = index % change_interval == 0
        head_models[unique_id] = Model(
            unique_id=unique_id,
            name=f"model_{index:05d}",
            columns=(
                {"id": "integer", "iteration_marker": "integer"}
                if changed
                else {"id": "integer"}
            ),
            dependencies=dependency,
            fingerprint=f"head-{index}" if changed else f"base-{index}",
            sql=(f"{sql}, 1::integer as iteration_marker" if changed else sql),
        )
    return (
        Manifest(path="synthetic-base", models=base_models, dialect="duckdb"),
        Manifest(path="synthetic-head", models=head_models, dialect="duckdb"),
    )


def _run_once(base: Manifest, head: Manifest) -> int:
    result = compare(base, head)
    result = add_sql_risk_findings(result, base, head)
    result = add_rename_candidates(result, base, head)
    result = add_column_lineage(result, head)
    return len(result.changes)


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def benchmark(size: int, iterations: int, warmups: int) -> BenchmarkResult:
    base, head = _manifest_pair(size)
    for _ in range(warmups):
        _run_once(base, head)
    durations: list[float] = []
    changed_models = 0
    for _ in range(iterations):
        gc.collect()
        started = time.perf_counter()
        changed_models = _run_once(base, head)
        durations.append(time.perf_counter() - started)
    return BenchmarkResult(
        models=size,
        changed_models=changed_models,
        iterations=iterations,
        median_seconds=statistics.median(durations),
        p95_seconds=_percentile(durations, 0.95),
        minimum_seconds=min(durations),
    )


def render(results: list[BenchmarkResult]) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Static-analysis benchmark results",
        "",
        f"Generated: {generated}",
        "",
        f"- Platform: {platform.system()} {platform.machine()}",
        f"- Python: {platform.python_version()}",
        f"- DuckDB: {duckdb.__version__}",
        f"- SQLGlot: {sqlglot.__version__}",
        "- Scenario: linear dependency graph with 1% changed models",
        "- Pipeline: manifest comparison, SQL risk checks, rename analysis, and column lineage",
        "",
        "| Models | Changed | Iterations | Minimum | Median | p95 | Target |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        target = "<30.000s" if result.models == 10_000 else "—"
        lines.append(
            f"| {result.models:,} | {result.changed_models:,} | "
            f"{result.iterations} | {result.minimum_seconds:.4f}s | "
            f"{result.median_seconds:.4f}s | {result.p95_seconds:.4f}s | {target} |"
        )
    lines.extend(
        [
            "",
            "These synthetic results are a regression baseline, not a promise for every project. "
            "Manifest shape, SQL complexity, hardware, and changed-model ratio materially affect runtime.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[100, 1_000, 10_000])
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.iterations <= 0 or args.warmups < 0:
        parser.error("iterations must be positive and warmups cannot be negative")
    report = render(
        [benchmark(size, args.iterations, args.warmups) for size in args.sizes]
    )
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
