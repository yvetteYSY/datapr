"""Conservative, advisory rename-candidate analysis."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace

from sqlglot import exp, parse_one
from sqlglot.errors import ParseError

from datapr.manifest import Manifest, Model
from datapr.models import Comparison, Finding, ModelChange


def _projection_signatures(model: Model, dialect: str | None) -> dict[str, str]:
    """Return canonical projection expressions keyed by output column name."""
    if not model.sql:
        return {}
    expression = parse_one(model.sql, read=dialect)
    select = expression if isinstance(expression, exp.Select) else expression.find(exp.Select)
    if select is None:
        return {}

    signatures: dict[str, str] = {}
    for projection in select.expressions:
        output_name = projection.alias_or_name
        if not output_name or isinstance(projection, exp.Star):
            continue
        body = projection.this if isinstance(projection, exp.Alias) else projection
        signatures[str(output_name)] = body.sql(dialect=dialect, pretty=False)
    return signatures


def _unique_pairs(matches: dict[str, set[str]]) -> tuple[list[tuple[str, str]], int]:
    """Keep only mutual one-to-one matches to avoid ambiguous suggestions."""
    reverse: dict[str, set[str]] = defaultdict(set)
    for before, afters in matches.items():
        for after in afters:
            reverse[after].add(before)
    pairs = sorted(
        (before, next(iter(afters)))
        for before, afters in matches.items()
        if len(afters) == 1 and len(reverse[next(iter(afters))]) == 1
    )
    return pairs, sum(len(afters) for afters in matches.values()) - len(pairs)


def _model_rename_findings(
    result: Comparison, base: Manifest, head: Manifest
) -> tuple[list[Finding], int]:
    removed = [change for change in result.changes if change.kind == "removed"]
    added = [change for change in result.changes if change.kind == "added"]
    removed_by_signature: dict[tuple[object, ...], list[Model]] = defaultdict(list)
    added_by_signature: dict[tuple[object, ...], list[Model]] = defaultdict(list)
    for before_change in removed:
        before = base.models[before_change.unique_id]
        if not before.fingerprint:
            continue
        signature = (before.fingerprint, tuple(sorted(before.columns.items())))
        removed_by_signature[signature].append(before)
    for after_change in added:
        after = head.models[after_change.unique_id]
        if not after.fingerprint:
            continue
        signature = (after.fingerprint, tuple(sorted(after.columns.items())))
        added_by_signature[signature].append(after)

    findings: list[Finding] = []
    ambiguous = 0
    for signature in sorted(
        removed_by_signature.keys() & added_by_signature.keys(), key=repr
    ):
        before_models = removed_by_signature[signature]
        after_models = added_by_signature[signature]
        if len(before_models) != 1 or len(after_models) != 1:
            ambiguous += len(before_models) * len(after_models)
            continue
        before, after = before_models[0], after_models[0]
        findings.append(
            Finding(
                id="rename.model_candidate",
                severity="info",
                model=after.name,
                message=f"Model `{before.name}` may have been renamed to `{after.name}`.",
                confidence=0.98,
                provenance="inferred",
                evidence={
                    "before_unique_id": before.unique_id,
                    "after_unique_id": after.unique_id,
                    "before_name": before.name,
                    "after_name": after.name,
                    "signals": ["identical_fingerprint", "identical_declared_schema"],
                    "blocking": False,
                },
            )
        )
    return findings, ambiguous


def _column_rename_findings(
    change: ModelChange,
    before: Model,
    after: Model,
    base_dialect: str | None,
    head_dialect: str | None,
) -> tuple[list[Finding], bool, int]:
    removed = [column for column in change.columns if column.kind == "removed"]
    added = [column for column in change.columns if column.kind == "added"]
    if not removed or not added or not before.sql or not after.sql:
        return [], False, 0

    try:
        base_signatures = _projection_signatures(before, base_dialect)
        head_signatures = _projection_signatures(after, head_dialect)
    except ParseError:
        return [], True, 0

    matches: dict[str, set[str]] = defaultdict(set)
    for old_column in removed:
        before_type = old_column.before
        before_signature = base_signatures.get(old_column.column)
        if not before_type or not before_signature:
            continue
        for new_column in added:
            if (
                new_column.after
                and before_type.casefold() == new_column.after.casefold()
                and before_signature == head_signatures.get(new_column.column)
            ):
                matches[old_column.column].add(new_column.column)

    findings: list[Finding] = []
    pairs, ambiguous = _unique_pairs(matches)
    for old_name, new_name in pairs:
        findings.append(
            Finding(
                id="rename.column_candidate",
                severity="info",
                model=after.name,
                message=f"Column `{old_name}` may have been renamed to `{new_name}`.",
                confidence=0.95,
                provenance="inferred",
                evidence={
                    "before_column": old_name,
                    "after_column": new_name,
                    "declared_type": before.columns[old_name],
                    "projection_expression": base_signatures[old_name],
                    "signals": [
                        "identical_projection_expression",
                        "identical_declared_type",
                    ],
                    "blocking": False,
                },
            )
        )
    return findings, False, ambiguous


def add_rename_candidates(
    result: Comparison, base: Manifest, head: Manifest
) -> Comparison:
    """Add high-precision rename hints without suppressing breaking findings."""
    rename_findings, ambiguous_pairs = _model_rename_findings(result, base, head)
    evaluated_models = 0
    parse_failures: list[str] = []

    for change in result.changes:
        if change.kind != "modified":
            continue
        before, after = base.models.get(change.unique_id), head.models.get(change.unique_id)
        if before is None or after is None:
            continue
        if any(column.kind == "removed" for column in change.columns) and any(
            column.kind == "added" for column in change.columns
        ):
            evaluated_models += 1
        candidates, parse_failed, ambiguous = _column_rename_findings(
            change, before, after, base.dialect, head.dialect
        )
        rename_findings.extend(candidates)
        ambiguous_pairs += ambiguous
        if parse_failed:
            parse_failures.append(after.name)

    coverage = dict(result.coverage)
    coverage["rename_analysis"] = {
        "complete": not parse_failures,
        "models_evaluated": evaluated_models,
        "parse_failures": sorted(parse_failures),
        "candidates": len(rename_findings),
        "ambiguous_pairs_skipped": ambiguous_pairs,
    }
    return replace(
        result,
        findings=tuple([*result.findings, *rename_findings]),
        coverage=coverage,
    )
