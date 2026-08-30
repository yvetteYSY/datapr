"""Bounded, local differential profiling powered by DuckDB."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import duckdb

from datapr.config import ExecutionConfig, PolicyConfig
from datapr.models import Comparison, Finding


SUPPORTED_EXTENSIONS = (".parquet", ".csv", ".json")
NUMERIC_TYPES = (
    "TINYINT",
    "SMALLINT",
    "INTEGER",
    "BIGINT",
    "HUGEINT",
    "UTINYINT",
    "USMALLINT",
    "UINTEGER",
    "UBIGINT",
    "FLOAT",
    "DOUBLE",
    "DECIMAL",
    "REAL",
)


class ProfileError(ValueError):
    """Raised when configured differential profiling cannot run."""


def _reader(path: Path) -> str:
    if path.suffix == ".parquet":
        return "read_parquet(?)"
    if path.suffix == ".csv":
        return "read_csv_auto(?, header=true)"
    if path.suffix == ".json":
        return "read_json_auto(?)"
    raise ProfileError(f"unsupported profile input: {path}")


def _find_model_file(directory: Path, model: str) -> Path | None:
    for extension in SUPPORTED_EXTENSIONS:
        candidate = directory / f"{model}{extension}"
        if candidate.is_file():
            return candidate
    return None


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _schema(connection: duckdb.DuckDBPyConnection, path: Path) -> dict[str, str]:
    rows = connection.execute(
        f"DESCRIBE SELECT * FROM {_reader(path)}", [str(path)]
    ).fetchall()
    return {str(row[0]): str(row[1]).upper() for row in rows}


def _row_count(connection: duckdb.DuckDBPyConnection, path: Path) -> int:
    return int(
        connection.execute(
            f"SELECT count(*) FROM {_reader(path)}", [str(path)]
        ).fetchone()[0]
    )


def _column_profile(
    connection: duckdb.DuckDBPyConnection,
    path: Path,
    column: str,
    data_type: str,
    sample_rows: int,
) -> dict[str, float | int | None]:
    quoted = _quote_identifier(column)
    source = _reader(path)
    parameters: list[Any] = [str(path), sample_rows]
    select = (
        f"count(*) AS sampled_rows, count({quoted}) AS non_null_rows"
    )
    if data_type.startswith(NUMERIC_TYPES):
        select += (
            f", avg({quoted})::DOUBLE AS mean, min({quoted})::DOUBLE AS minimum, "
            f"max({quoted})::DOUBLE AS maximum"
        )
    row = connection.execute(
        f"SELECT {select} FROM (SELECT * FROM {source} LIMIT ?)", parameters
    ).fetchone()
    sampled = int(row[0])
    non_null = int(row[1])
    result: dict[str, float | int | None] = {
        "sampled_rows": sampled,
        "null_rate_percent": (
            round((sampled - non_null) * 100.0 / sampled, 4) if sampled else 0.0
        ),
    }
    if len(row) > 2:
        result.update(mean=row[2], minimum=row[3], maximum=row[4])
    return result


def _percent_change(before: float, after: float) -> float:
    if before == 0:
        return 0.0 if after == 0 else 100.0
    return abs(after - before) * 100.0 / abs(before)


def _profile_pair(
    model: str,
    base_path: Path,
    head_path: Path,
    execution: ExecutionConfig,
    policy: PolicyConfig,
) -> list[Finding]:
    connection = duckdb.connect(":memory:")
    try:
        base_count = _row_count(connection, base_path)
        head_count = _row_count(connection, head_path)
        row_change = _percent_change(float(base_count), float(head_count))
        findings: list[Finding] = []
        if base_count != head_count:
            findings.append(
                Finding(
                    id="profile.row_count_changed",
                    severity=(
                        "medium"
                        if row_change >= policy.row_count_change_percent
                        else "low"
                    ),
                    model=model,
                    message=(
                        f"Row count changed from {base_count:,} to {head_count:,} "
                        f"({row_change:.2f}%)."
                    ),
                    confidence=1.0,
                    provenance="observed",
                    evidence={
                        "before": base_count,
                        "after": head_count,
                        "change_percent": round(row_change, 4),
                    },
                )
            )

        base_schema, head_schema = _schema(connection, base_path), _schema(
            connection, head_path
        )
        for column in sorted(base_schema.keys() & head_schema.keys()):
            base_profile = _column_profile(
                connection,
                base_path,
                column,
                base_schema[column],
                execution.sample_rows,
            )
            head_profile = _column_profile(
                connection,
                head_path,
                column,
                head_schema[column],
                execution.sample_rows,
            )
            null_delta = abs(
                float(head_profile["null_rate_percent"])
                - float(base_profile["null_rate_percent"])
            )
            if null_delta > 0:
                findings.append(
                    Finding(
                        id="profile.null_rate_changed",
                        severity=(
                            "medium"
                            if null_delta >= policy.null_rate_change_percent
                            else "low"
                        ),
                        model=model,
                        message=(
                            f"`{column}` null rate changed by "
                            f"{null_delta:.2f} percentage points."
                        ),
                        confidence=1.0,
                        provenance="observed",
                        evidence={
                            "column": column,
                            "before": base_profile["null_rate_percent"],
                            "after": head_profile["null_rate_percent"],
                            "change_percentage_points": round(null_delta, 4),
                            "sample_rows": execution.sample_rows,
                        },
                    )
                )
            before_mean, after_mean = base_profile.get("mean"), head_profile.get("mean")
            if before_mean is not None and after_mean is not None:
                mean_change = _percent_change(float(before_mean), float(after_mean))
                if mean_change >= policy.distribution_change_percent:
                    findings.append(
                        Finding(
                            id="profile.distribution_changed",
                            severity="medium",
                            model=model,
                            message=(
                                f"`{column}` mean changed by {mean_change:.2f}% "
                                "in the bounded sample."
                            ),
                            confidence=0.9,
                            provenance="observed",
                            evidence={
                                "column": column,
                                "base_profile": base_profile,
                                "head_profile": head_profile,
                                "mean_change_percent": round(mean_change, 4),
                            },
                        )
                    )
        return findings
    except duckdb.Error as exc:
        raise ProfileError(f"cannot profile model {model}: {exc}") from exc
    finally:
        connection.close()


def add_profile_findings(
    result: Comparison,
    execution: ExecutionConfig,
    policy: PolicyConfig,
) -> Comparison:
    if not execution.base_data_dir and not execution.head_data_dir:
        return result
    if not execution.base_data_dir or not execution.head_data_dir:
        raise ProfileError("both base_data_dir and head_data_dir are required")
    base_dir, head_dir = Path(execution.base_data_dir), Path(execution.head_data_dir)
    if not base_dir.is_dir() or not head_dir.is_dir():
        raise ProfileError("configured base and head data directories must exist")

    findings = list(result.findings)
    profiled, missing = 0, []
    for change in result.changes:
        if change.kind == "added" or change.kind == "removed":
            continue
        base_file = _find_model_file(base_dir, change.name)
        head_file = _find_model_file(head_dir, change.name)
        if not base_file or not head_file:
            missing.append(change.name)
            continue
        findings.extend(
            _profile_pair(change.name, base_file, head_file, execution, policy)
        )
        profiled += 1

    coverage = dict(result.coverage)
    coverage.update(
        differential_execution=True,
        profiled_models=profiled,
        missing_profile_models=missing,
        sample_rows=execution.sample_rows,
        complete=not missing,
    )
    return replace(result, findings=tuple(findings), coverage=coverage)
