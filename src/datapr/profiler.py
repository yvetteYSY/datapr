"""Bounded, local differential profiling powered by DuckDB."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

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


def _validate_execution_limits(execution: ExecutionConfig) -> None:
    positive_limits = {
        "sample_rows": execution.sample_rows,
        "max_sample_rows": execution.max_sample_rows,
        "max_profile_models": execution.max_profile_models,
        "max_profile_file_bytes": execution.max_profile_file_bytes,
        "max_profile_columns": execution.max_profile_columns,
        "memory_limit_mb": execution.memory_limit_mb,
    }
    invalid = [name for name, value in positive_limits.items() if value <= 0]
    if invalid:
        raise ProfileError(f"execution limits must be positive: {', '.join(invalid)}")
    if execution.sample_rows > execution.max_sample_rows:
        raise ProfileError("sample_rows cannot exceed max_sample_rows")


def _validate_profile_input(path: Path, execution: ExecutionConfig) -> None:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ProfileError(f"cannot inspect profile input {path}: {exc}") from exc
    if size > execution.max_profile_file_bytes:
        raise ProfileError(
            f"profile input {path} is {size:,} bytes; limit is "
            f"{execution.max_profile_file_bytes:,}"
        )


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


def _sample_relation(
    connection: duckdb.DuckDBPyConnection,
    relation: str,
    path: Path,
    columns: list[str],
    execution: ExecutionConfig,
) -> None:
    source = _reader(path)
    target = _quote_identifier(relation)
    if execution.sample_strategy == "first":
        connection.execute(
            f"CREATE TEMP TABLE {target} AS "
            f"SELECT * FROM {source} LIMIT ?",
            [str(path), execution.sample_rows],
        )
        return
    if execution.sample_strategy != "hash":
        raise ProfileError(
            f"unsupported sample strategy: {execution.sample_strategy}"
        )
    if not columns:
        raise ProfileError(f"cannot hash-sample input without columns: {path}")

    fields = ", ".join(
        f"{_quote_identifier(column)} := {_quote_identifier(column)}"
        for column in columns
    )
    connection.execute(
        f"CREATE TEMP TABLE {target} AS "
        f"SELECT * FROM {source} "
        "ORDER BY md5(concat(cast(? AS VARCHAR), ':', "
        f"to_json(struct_pack({fields})))) LIMIT ?",
        [str(path), execution.sample_seed, execution.sample_rows],
    )


def _column_profile(
    connection: duckdb.DuckDBPyConnection,
    relation: str,
    column: str,
    data_type: str,
) -> dict[str, float | int | None]:
    quoted = _quote_identifier(column)
    source = _quote_identifier(relation)
    select = (
        f"count(*) AS sampled_rows, count({quoted}) AS non_null_rows"
    )
    if data_type.startswith(NUMERIC_TYPES):
        select += (
            f", avg({quoted})::DOUBLE AS mean, min({quoted})::DOUBLE AS minimum, "
            f"max({quoted})::DOUBLE AS maximum"
        )
    row = connection.execute(f"SELECT {select} FROM {source}").fetchone()
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
        connection.execute("SET threads = 1")
        connection.execute(
            f"SET memory_limit = '{execution.memory_limit_mb}MB'"
        )
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

        base_schema = _schema(connection, base_path)
        head_schema = _schema(connection, head_path)
        if len(base_schema) > execution.max_profile_columns:
            raise ProfileError(
                f"profile input {base_path} contains {len(base_schema):,} columns; "
                f"limit is {execution.max_profile_columns:,}"
            )
        if len(head_schema) > execution.max_profile_columns:
            raise ProfileError(
                f"profile input {head_path} contains {len(head_schema):,} columns; "
                f"limit is {execution.max_profile_columns:,}"
            )
        shared_columns = sorted(base_schema.keys() & head_schema.keys())
        sampling_evidence = {
            "sample_rows": execution.sample_rows,
            "sample_strategy": execution.sample_strategy,
            "sample_seed": execution.sample_seed,
            "sample_hash": (
                "md5-json-v1" if execution.sample_strategy == "hash" else None
            ),
            "sample_columns": shared_columns,
        }
        _sample_relation(
            connection,
            "datapr_base_sample",
            base_path,
            shared_columns or sorted(base_schema),
            execution,
        )
        _sample_relation(
            connection,
            "datapr_head_sample",
            head_path,
            shared_columns or sorted(head_schema),
            execution,
        )
        for column in sorted(base_schema.keys() & head_schema.keys()):
            base_profile = _column_profile(
                connection,
                "datapr_base_sample",
                column,
                base_schema[column],
            )
            head_profile = _column_profile(
                connection,
                "datapr_head_sample",
                column,
                head_schema[column],
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
                            **sampling_evidence,
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
                                **sampling_evidence,
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
    _validate_execution_limits(execution)
    if not execution.base_data_dir and not execution.head_data_dir:
        return result
    if not execution.base_data_dir or not execution.head_data_dir:
        raise ProfileError("both base_data_dir and head_data_dir are required")
    base_dir, head_dir = Path(execution.base_data_dir), Path(execution.head_data_dir)
    if not base_dir.is_dir() or not head_dir.is_dir():
        raise ProfileError("configured base and head data directories must exist")

    eligible_changes = [
        change
        for change in result.changes
        if change.kind not in {"added", "removed"}
    ]
    if len(eligible_changes) > execution.max_profile_models:
        raise ProfileError(
            f"comparison contains {len(eligible_changes):,} profile-eligible models; "
            f"limit is {execution.max_profile_models:,}"
        )

    findings = list(result.findings)
    profiled, missing = 0, []
    for change in eligible_changes:
        base_file = _find_model_file(base_dir, change.name)
        head_file = _find_model_file(head_dir, change.name)
        if not base_file or not head_file:
            missing.append(change.name)
            continue
        _validate_profile_input(base_file, execution)
        _validate_profile_input(head_file, execution)
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
        sample_strategy=execution.sample_strategy,
        sample_seed=execution.sample_seed,
        sample_hash=(
            "md5-json-v1" if execution.sample_strategy == "hash" else None
        ),
        profile_threads=1,
        profile_memory_limit_mb=execution.memory_limit_mb,
        max_profile_file_bytes=execution.max_profile_file_bytes,
        max_profile_columns=execution.max_profile_columns,
        max_profile_models=execution.max_profile_models,
        complete=bool(coverage.get("complete", True)) and not missing,
    )
    return replace(result, findings=tuple(findings), coverage=coverage)
