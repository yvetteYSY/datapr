"""Configuration loading with safe, explicit defaults."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when DataPR configuration is invalid."""


@dataclass(frozen=True)
class PolicyConfig:
    fail_on: frozenset[str] = frozenset(
        {"model.removed", "schema.removed_column", "schema.incompatible_type_change"}
    )
    warn_on: frozenset[str] = frozenset(
        {
            "model.modified",
            "performance.filter_removed",
            "performance.cross_join_added",
            "performance.select_star_added",
        }
    )
    downstream_models: int = 10
    row_count_change_percent: float = 5.0
    null_rate_change_percent: float = 5.0
    distribution_change_percent: float = 10.0
    fail_on_incomplete_coverage: bool = False


@dataclass(frozen=True)
class ExecutionConfig:
    sample_rows: int = 100_000
    sample_strategy: str = "hash"
    sample_seed: int = 0
    max_sample_rows: int = 1_000_000
    max_profile_models: int = 100
    max_profile_file_bytes: int = 1024 * 1024 * 1024
    max_profile_columns: int = 1_000
    memory_limit_mb: int = 512
    base_data_dir: str | None = None
    head_data_dir: str | None = None


@dataclass(frozen=True)
class DataPRConfig:
    policy: PolicyConfig = PolicyConfig()
    execution: ExecutionConfig = ExecutionConfig()


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"'{field}' must be a mapping")
    return value


def _reject_unknown(
    mapping: dict[str, Any], allowed: set[str], field: str
) -> None:
    unknown = sorted(
        str(key) for key in mapping if not isinstance(key, str) or key not in allowed
    )
    if unknown:
        raise ConfigError(f"unknown '{field}' field(s): {', '.join(unknown)}")


def _string_set(value: Any, field: str, default: frozenset[str]) -> frozenset[str]:
    if value is None:
        return default
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"'{field}' must be a list of finding IDs")
    if len(value) != len(set(value)):
        raise ConfigError(f"'{field}' must not contain duplicate finding IDs")
    return frozenset(value)


def _positive_int(value: Any, field: str, default: int) -> int:
    result = default if value is None else value
    if isinstance(result, bool) or not isinstance(result, int):
        raise ConfigError(f"'{field}' must be an integer")
    if result <= 0:
        raise ConfigError(f"'{field}' must be positive")
    return result


def _integer(value: Any, field: str, default: int) -> int:
    result = default if value is None else value
    if isinstance(result, bool) or not isinstance(result, int):
        raise ConfigError(f"'{field}' must be an integer")
    return result


def _nonnegative_int(value: Any, field: str, default: int) -> int:
    result = default if value is None else value
    if isinstance(result, bool) or not isinstance(result, int):
        raise ConfigError(f"'{field}' must be an integer")
    if result < 0:
        raise ConfigError(f"'{field}' must be non-negative")
    return result


def _nonnegative_float(value: Any, field: str, default: float) -> float:
    raw = default if value is None else value
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise ConfigError(f"'{field}' must be a number")
    result = float(raw)
    if not math.isfinite(result):
        raise ConfigError(f"'{field}' must be finite")
    if result < 0:
        raise ConfigError(f"'{field}' must be non-negative")
    return result


def _boolean(value: Any, field: str, default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ConfigError(f"'{field}' must be a boolean")
    return value


def _optional_string(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ConfigError(f"'{field}' must be a non-empty string")
    return value


def load_config(path: str | Path | None) -> DataPRConfig:
    if path is None:
        return DataPRConfig()
    config_path = Path(path)
    try:
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        payload = {} if loaded is None else loaded
    except FileNotFoundError as exc:
        raise ConfigError(f"config not found: {config_path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML in {config_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ConfigError("configuration root must be a mapping")
    _reject_unknown(payload, {"version", "policies", "execution"}, "root")
    version = payload.get("version", 1)
    if isinstance(version, bool) or version != 1:
        raise ConfigError("only configuration version 1 is supported")

    policies = _mapping(payload.get("policies"), "policies")
    execution = _mapping(payload.get("execution"), "execution")
    _reject_unknown(
        policies,
        {
            "fail_on",
            "warn_on",
            "downstream_models",
            "row_count_change_percent",
            "null_rate_change_percent",
            "distribution_change_percent",
            "fail_on_incomplete_coverage",
        },
        "policies",
    )
    _reject_unknown(
        execution,
        {
            "sample_rows",
            "sample_strategy",
            "sample_seed",
            "max_sample_rows",
            "max_profile_models",
            "max_profile_file_bytes",
            "max_profile_columns",
            "memory_limit_mb",
            "base_data_dir",
            "head_data_dir",
        },
        "execution",
    )
    defaults = PolicyConfig()
    policy = PolicyConfig(
        fail_on=_string_set(policies.get("fail_on"), "policies.fail_on", defaults.fail_on),
        warn_on=_string_set(policies.get("warn_on"), "policies.warn_on", defaults.warn_on),
        downstream_models=_nonnegative_int(
            policies.get("downstream_models"),
            "policies.downstream_models",
            defaults.downstream_models,
        ),
        row_count_change_percent=_nonnegative_float(
            policies.get("row_count_change_percent"),
            "policies.row_count_change_percent",
            defaults.row_count_change_percent,
        ),
        null_rate_change_percent=_nonnegative_float(
            policies.get("null_rate_change_percent"),
            "policies.null_rate_change_percent",
            defaults.null_rate_change_percent,
        ),
        distribution_change_percent=_nonnegative_float(
            policies.get("distribution_change_percent"),
            "policies.distribution_change_percent",
            defaults.distribution_change_percent,
        ),
        fail_on_incomplete_coverage=_boolean(
            policies.get("fail_on_incomplete_coverage"),
            "policies.fail_on_incomplete_coverage",
            defaults.fail_on_incomplete_coverage,
        ),
    )
    defaults_execution = ExecutionConfig()
    sample_rows = _positive_int(
        execution.get("sample_rows"),
        "execution.sample_rows",
        defaults_execution.sample_rows,
    )
    max_sample_rows = _positive_int(
        execution.get("max_sample_rows"),
        "execution.max_sample_rows",
        defaults_execution.max_sample_rows,
    )
    if sample_rows > max_sample_rows:
        raise ConfigError("execution.sample_rows cannot exceed execution.max_sample_rows")
    sample_seed = _integer(
        execution.get("sample_seed"),
        "execution.sample_seed",
        defaults_execution.sample_seed,
    )
    sample_strategy = str(execution.get("sample_strategy", "hash")).casefold()
    if sample_strategy not in {"hash", "first"}:
        raise ConfigError("execution.sample_strategy must be 'hash' or 'first'")
    return DataPRConfig(
        policy=policy,
        execution=ExecutionConfig(
            sample_rows=sample_rows,
            sample_strategy=sample_strategy,
            sample_seed=sample_seed,
            max_sample_rows=max_sample_rows,
            max_profile_models=_positive_int(
                execution.get("max_profile_models"),
                "execution.max_profile_models",
                defaults_execution.max_profile_models,
            ),
            max_profile_file_bytes=_positive_int(
                execution.get("max_profile_file_bytes"),
                "execution.max_profile_file_bytes",
                defaults_execution.max_profile_file_bytes,
            ),
            max_profile_columns=_positive_int(
                execution.get("max_profile_columns"),
                "execution.max_profile_columns",
                defaults_execution.max_profile_columns,
            ),
            memory_limit_mb=_positive_int(
                execution.get("memory_limit_mb"),
                "execution.memory_limit_mb",
                defaults_execution.memory_limit_mb,
            ),
            base_data_dir=_optional_string(
                execution.get("base_data_dir"), "execution.base_data_dir"
            ),
            head_data_dir=_optional_string(
                execution.get("head_data_dir"), "execution.head_data_dir"
            ),
        ),
    )
