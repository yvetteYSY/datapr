"""Best-effort column lineage for common SQL select projections."""

from __future__ import annotations

from dataclasses import replace

from sqlglot import exp, parse_one
from sqlglot.errors import ParseError

from datapr.manifest import Manifest
from datapr.models import Comparison, Finding


def _projection_lineage(sql: str) -> dict[str, list[str]]:
    expression = parse_one(sql)
    select = expression if isinstance(expression, exp.Select) else expression.find(exp.Select)
    if select is None:
        return {}
    lineage: dict[str, list[str]] = {}
    for projection in select.expressions:
        output_name = projection.alias_or_name
        if not output_name or isinstance(projection, exp.Star):
            continue
        sources: set[str] = set()
        for column in projection.find_all(exp.Column):
            source = f"{column.table}.{column.name}" if column.table else column.name
            sources.add(source)
        lineage[str(output_name)] = sorted(sources)
    return lineage


def add_column_lineage(result: Comparison, manifest: Manifest) -> Comparison:
    mappings: dict[str, dict[str, list[str]]] = {}
    findings = list(result.findings)
    missing: list[str] = []
    parse_failures: list[str] = []
    changed_ids = {change.unique_id for change in result.changes if change.kind != "removed"}
    for unique_id in sorted(changed_ids):
        model = manifest.models.get(unique_id)
        if model is None or not model.sql:
            missing.append(model.name if model else unique_id)
            continue
        try:
            mappings[model.name] = _projection_lineage(model.sql)
        except ParseError as exc:
            parse_failures.append(model.name)
            findings.append(
                Finding(
                    id="lineage.sql_parse_incomplete",
                    severity="medium",
                    model=model.name,
                    message="Column lineage is incomplete because SQL parsing failed.",
                    confidence=1.0,
                    provenance="observed",
                    evidence={"error": str(exc)[:300]},
                )
            )

    coverage = dict(result.coverage)
    coverage.update(
        column_lineage_models=len(mappings),
        missing_sql_models=missing,
        sql_parse_failures=parse_failures,
    )
    if missing or parse_failures:
        coverage["complete"] = False
    return replace(
        result,
        findings=tuple(findings),
        coverage=coverage,
        column_lineage=mappings,
    )
