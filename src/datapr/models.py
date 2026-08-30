"""Stable result types shared by analyzers, policies, and renderers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
DECISION_ORDER = {"pass": 0, "warn": 1, "fail": 2}


@dataclass(frozen=True)
class ColumnChange:
    column: str
    kind: str
    before: str | None = None
    after: str | None = None


@dataclass(frozen=True)
class ModelChange:
    unique_id: str
    name: str
    kind: str
    columns: tuple[ColumnChange, ...]
    downstream: tuple[str, ...]


@dataclass(frozen=True)
class Finding:
    id: str
    severity: str
    model: str
    message: str
    confidence: float
    provenance: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Comparison:
    schema_version: str
    base_manifest: str
    head_manifest: str
    models_base: int
    models_head: int
    changes: tuple[ModelChange, ...]
    findings: tuple[Finding, ...] = ()
    coverage: dict[str, Any] = field(default_factory=dict)
    column_lineage: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    decision: str = "pass"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
