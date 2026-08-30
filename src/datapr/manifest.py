"""Load the small, stable subset of dbt artifacts DataPR needs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ManifestError(ValueError):
    """Raised when a dbt manifest cannot be understood."""


@dataclass(frozen=True)
class Model:
    unique_id: str
    name: str
    columns: dict[str, str | None]
    dependencies: frozenset[str]
    fingerprint: str | None
    sql: str | None


@dataclass(frozen=True)
class Manifest:
    path: str
    models: dict[str, Model]
    dialect: str | None = None


@dataclass(frozen=True)
class ManifestLimits:
    max_bytes: int = 100 * 1024 * 1024
    max_nodes: int = 100_000
    max_columns_per_model: int = 10_000
    max_sql_chars: int = 10_000_000


DEFAULT_MANIFEST_LIMITS = ManifestLimits()


def _fingerprint(node: dict[str, Any]) -> str | None:
    checksum = node.get("checksum")
    if isinstance(checksum, dict) and checksum.get("checksum"):
        return str(checksum["checksum"])
    for field in ("compiled_code", "compiled_sql", "raw_code", "raw_sql"):
        if node.get(field) is not None:
            return str(node[field])
    return None


def _model_sql(
    node: dict[str, Any], unique_id: str, source: str, limits: ManifestLimits
) -> str | None:
    for field in ("compiled_code", "compiled_sql", "raw_code", "raw_sql"):
        value = node.get(field)
        if value is None:
            continue
        if not isinstance(value, str):
            raise ManifestError(f"{source} model {unique_id} field '{field}' must be text")
        if len(value) > limits.max_sql_chars:
            raise ManifestError(
                f"{source} model {unique_id} SQL exceeds "
                f"{limits.max_sql_chars:,} characters"
            )
        return value
    return None


def _from_payload(
    payload: Any, source: str, limits: ManifestLimits = DEFAULT_MANIFEST_LIMITS
) -> Manifest:
    if not isinstance(payload, dict):
        raise ManifestError(f"{source} does not contain a JSON object")
    nodes = payload.get("nodes")
    if not isinstance(nodes, dict):
        raise ManifestError(f"{source} does not contain a dbt 'nodes' object")
    if len(nodes) > limits.max_nodes:
        raise ManifestError(
            f"{source} contains {len(nodes):,} nodes; limit is {limits.max_nodes:,}"
        )

    models: dict[str, Model] = {}
    for unique_id, node in nodes.items():
        if not isinstance(node, dict):
            raise ManifestError(f"{source} node {unique_id!s} must be an object")
        if node.get("resource_type") != "model":
            continue
        if not isinstance(unique_id, str):
            raise ManifestError(f"{source} contains a model with a non-text unique_id")
        raw_columns = node.get("columns")
        if raw_columns is None:
            raw_columns = {}
        if not isinstance(raw_columns, dict):
            raise ManifestError(f"{source} model {unique_id} columns must be an object")
        if len(raw_columns) > limits.max_columns_per_model:
            raise ManifestError(
                f"{source} model {unique_id} contains {len(raw_columns):,} columns; "
                f"limit is {limits.max_columns_per_model:,}"
            )
        invalid_columns = [
            str(name) for name, value in raw_columns.items() if not isinstance(value, dict)
        ]
        if invalid_columns:
            raise ManifestError(
                f"{source} model {unique_id} column metadata must be objects: "
                f"{', '.join(sorted(invalid_columns)[:3])}"
            )
        columns = {
            str(name): (str(value.get("data_type")) if value.get("data_type") else None)
            for name, value in raw_columns.items()
        }
        depends_on = node.get("depends_on")
        if depends_on is None:
            depends_on = {}
        if not isinstance(depends_on, dict):
            raise ManifestError(f"{source} model {unique_id} depends_on must be an object")
        dependencies = depends_on.get("nodes")
        if dependencies is None:
            dependencies = []
        if not isinstance(dependencies, list) or not all(
            isinstance(item, str) for item in dependencies
        ):
            raise ManifestError(
                f"{source} model {unique_id} dependencies must be a list of strings"
            )
        sql = _model_sql(node, unique_id, source, limits)
        models[unique_id] = Model(
            unique_id=unique_id,
            name=str(node.get("name") or unique_id),
            columns=columns,
            dependencies=frozenset(dependencies),
            fingerprint=_fingerprint(node),
            sql=sql,
        )
    metadata = payload.get("metadata")
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise ManifestError(f"{source} metadata must be an object")
    adapter_type = metadata.get("adapter_type")
    dialect_aliases = {
        "postgresql": "postgres",
        "databricks": "databricks",
    }
    dialect = dialect_aliases.get(str(adapter_type), str(adapter_type)) if adapter_type else None
    return Manifest(path=source, models=models, dialect=dialect)


def load_manifest_text(
    text: str,
    source: str = "<memory>",
    *,
    limits: ManifestLimits = DEFAULT_MANIFEST_LIMITS,
) -> Manifest:
    size = len(text.encode("utf-8"))
    if size > limits.max_bytes:
        raise ManifestError(
            f"{source} is {size:,} bytes; limit is {limits.max_bytes:,}"
        )
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ManifestError(f"invalid JSON in {source}: {exc}") from exc
    return _from_payload(payload, source, limits)


def load_manifest(
    path: str | Path, *, limits: ManifestLimits = DEFAULT_MANIFEST_LIMITS
) -> Manifest:
    manifest_path = Path(path)
    try:
        size = manifest_path.stat().st_size
        if size > limits.max_bytes:
            raise ManifestError(
                f"{manifest_path} is {size:,} bytes; limit is {limits.max_bytes:,}"
            )
        text = manifest_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ManifestError(f"manifest not found: {manifest_path}") from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise ManifestError(f"cannot read manifest {manifest_path}: {exc}") from exc
    return load_manifest_text(text, str(manifest_path), limits=limits)
