"""Deterministic comparison of normalized dbt manifests."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass

from datapr.manifest import Manifest, Model


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
class Comparison:
    schema_version: str
    base_manifest: str
    head_manifest: str
    models_base: int
    models_head: int
    changes: tuple[ModelChange, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _column_changes(base: Model, head: Model) -> tuple[ColumnChange, ...]:
    changes: list[ColumnChange] = []
    for column in sorted(base.columns.keys() - head.columns.keys()):
        changes.append(ColumnChange(column, "removed", before=base.columns[column]))
    for column in sorted(base.columns.keys() & head.columns.keys()):
        before, after = base.columns[column], head.columns[column]
        if before != after:
            changes.append(ColumnChange(column, "type_changed", before, after))
    for column in sorted(head.columns.keys() - base.columns.keys()):
        changes.append(ColumnChange(column, "added", after=head.columns[column]))
    return tuple(changes)


def _reverse_graph(manifest: Manifest) -> dict[str, set[str]]:
    reverse: dict[str, set[str]] = {}
    for model in manifest.models.values():
        for dependency in model.dependencies:
            reverse.setdefault(dependency, set()).add(model.unique_id)
    return reverse


def _downstream(unique_id: str, *manifests: Manifest) -> tuple[str, ...]:
    combined: dict[str, set[str]] = {}
    names: dict[str, str] = {}
    for manifest in manifests:
        names.update({key: model.name for key, model in manifest.models.items()})
        for parent, children in _reverse_graph(manifest).items():
            combined.setdefault(parent, set()).update(children)

    seen: set[str] = set()
    queue = deque(sorted(combined.get(unique_id, set())))
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        queue.extend(sorted(combined.get(current, set()) - seen))
    return tuple(sorted(names.get(item, item) for item in seen))


def compare(base: Manifest, head: Manifest) -> Comparison:
    changes: list[ModelChange] = []
    all_ids = sorted(base.models.keys() | head.models.keys())
    for unique_id in all_ids:
        before, after = base.models.get(unique_id), head.models.get(unique_id)
        if before is None and after is not None:
            kind, columns, model = "added", (), after
        elif before is not None and after is None:
            kind, columns, model = "removed", (), before
        elif before is not None and after is not None:
            columns = _column_changes(before, after)
            changed = (
                before.fingerprint != after.fingerprint
                or before.dependencies != after.dependencies
                or bool(columns)
            )
            if not changed:
                continue
            kind, model = "modified", after
        else:  # pragma: no cover - exhaustive guard
            continue
        changes.append(
            ModelChange(
                unique_id=unique_id,
                name=model.name,
                kind=kind,
                columns=columns,
                downstream=_downstream(unique_id, base, head),
            )
        )

    return Comparison(
        schema_version="0.1",
        base_manifest=str(base.path),
        head_manifest=str(head.path),
        models_base=len(base.models),
        models_head=len(head.models),
        changes=tuple(changes),
    )
