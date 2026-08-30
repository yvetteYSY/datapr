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


def _fingerprint(node: dict[str, Any]) -> str | None:
    checksum = node.get("checksum")
    if isinstance(checksum, dict) and checksum.get("checksum"):
        return str(checksum["checksum"])
    for field in ("compiled_code", "compiled_sql", "raw_code", "raw_sql"):
        if node.get(field) is not None:
            return str(node[field])
    return None


def _from_payload(payload: Any, source: str) -> Manifest:
    if not isinstance(payload, dict):
        raise ManifestError(f"{source} does not contain a JSON object")
    nodes = payload.get("nodes")
    if not isinstance(nodes, dict):
        raise ManifestError(f"{source} does not contain a dbt 'nodes' object")

    models: dict[str, Model] = {}
    for unique_id, node in nodes.items():
        if not isinstance(node, dict) or node.get("resource_type") != "model":
            continue
        raw_columns = node.get("columns") or {}
        columns = {
            str(name): (str(value.get("data_type")) if value.get("data_type") else None)
            for name, value in raw_columns.items()
            if isinstance(value, dict)
        }
        depends_on = node.get("depends_on") or {}
        dependencies = depends_on.get("nodes") or []
        models[str(unique_id)] = Model(
            unique_id=str(unique_id),
            name=str(node.get("name") or unique_id),
            columns=columns,
            dependencies=frozenset(str(item) for item in dependencies),
            fingerprint=_fingerprint(node),
            sql=next(
                (
                    str(node[field])
                    for field in ("compiled_code", "compiled_sql", "raw_code", "raw_sql")
                    if node.get(field) is not None
                ),
                None,
            ),
        )
    return Manifest(path=source, models=models)


def load_manifest_text(text: str, source: str = "<memory>") -> Manifest:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ManifestError(f"invalid JSON in {source}: {exc}") from exc
    return _from_payload(payload, source)


def load_manifest(path: str | Path) -> Manifest:
    manifest_path = Path(path)
    try:
        text = manifest_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ManifestError(f"manifest not found: {manifest_path}") from exc
    return load_manifest_text(text, str(manifest_path))
