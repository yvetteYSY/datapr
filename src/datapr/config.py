"""Configuration loading with safe, explicit defaults."""

from __future__ import annotations

from dataclasses import dataclass
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


def _string_set(value: Any, field: str, default: frozenset[str]) -> frozenset[str]:
    if value is None:
        return default
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"'{field}' must be a list of finding IDs")
    return frozenset(value)


def _positive_int(value: Any, field: str, default: int) -> int:
    try:
        result = int(default if value is None else value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"'{field}' must be an integer") from exc
    if result <= 0:
        raise ConfigError(f"'{field}' must be positive")
    return result


def load_config(path: str | Path | None) -> DataPRConfig:
    if path is None:
        return DataPRConfig()
    config_path = Path(path)
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError as exc:
        raise ConfigError(f"config not found: {config_path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML in {config_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ConfigError("configuration root must be a mapping")
    if payload.get("version", 1) != 1:
        raise ConfigError("only configuration version 1 is supported")

    policies = _mapping(payload.get("policies"), "policies")
    execution = _mapping(payload.get("execution"), "execution")
    defaults = PolicyConfig()
    policy = PolicyConfig(
        fail_on=_string_set(policies.get("fail_on"), "policies.fail_on", defaults.fail_on),
        warn_on=_string_set(policies.get("warn_on"), "policies.warn_on", defaults.warn_on),
        downstream_models=int(
            policies.get("downstream_models", defaults.downstream_models)
        ),
        row_count_change_percent=float(
            policies.get(
                "row_count_change_percent", defaults.row_count_change_percent
            )
        ),
        null_rate_change_percent=float(
            policies.get(
                "null_rate_change_percent", defaults.null_rate_change_percent
            )
        ),
        distribution_change_percent=float(
            policies.get(
                "distribution_change_percent",
                defaults.distribution_change_percent,
            )
        ),
        fail_on_incomplete_coverage=bool(
            policies.get(
                "fail_on_incomplete_coverage", defaults.fail_on_incomplete_coverage
            )
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
    try:
        sample_seed = int(execution.get("sample_seed", defaults_execution.sample_seed))
    except (TypeError, ValueError) as exc:
        raise ConfigError("'execution.sample_seed' must be an integer") from exc
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
            base_data_dir=execution.get("base_data_dir"),
            head_data_dir=execution.get("head_data_dir"),
        ),
    )
