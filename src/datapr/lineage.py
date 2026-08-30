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


def _sql_risk_stats(sql: str) -> dict[str, int | bool]:
    expression = parse_one(sql)
    return {
        "has_filter": expression.find(exp.Where) is not None,
        "cross_joins": sum(
            1
            for join in expression.find_all(exp.Join)
            if str(join.args.get("kind") or "").upper() == "CROSS"
        ),
        "select_stars": sum(1 for _ in expression.find_all(exp.Star)),
    }


def add_sql_risk_findings(
    result: Comparison, base: Manifest, head: Manifest
) -> Comparison:
    findings = list(result.findings)
    for change in result.changes:
        if change.kind != "modified":
            continue
        before, after = base.models.get(change.unique_id), head.models.get(change.unique_id)
        if before is None or after is None or not before.sql or not after.sql:
            continue
        try:
            base_stats, head_stats = _sql_risk_stats(before.sql), _sql_risk_stats(after.sql)
        except ParseError:
            continue
        if base_stats["has_filter"] and not head_stats["has_filter"]:
            findings.append(
                Finding(
                    id="performance.filter_removed",
                    severity="high",
                    model=after.name,
                    message="A filtering predicate was removed; scanned data may increase.",
                    confidence=0.8,
                    provenance="inferred",
                    evidence={"before": base_stats, "after": head_stats},
                )
            )
        if int(head_stats["cross_joins"]) > int(base_stats["cross_joins"]):
            findings.append(
                Finding(
                    id="performance.cross_join_added",
                    severity="high",
                    model=after.name,
                    message="A cross join was added; cardinality and cost may increase.",
                    confidence=0.9,
                    provenance="inferred",
                    evidence={"before": base_stats, "after": head_stats},
                )
            )
        if int(head_stats["select_stars"]) > int(base_stats["select_stars"]):
            findings.append(
                Finding(
                    id="performance.select_star_added",
                    severity="medium",
                    model=after.name,
                    message="A wildcard projection was added and may scan unnecessary columns.",
                    confidence=0.7,
                    provenance="inferred",
                    evidence={"before": base_stats, "after": head_stats},
                )
            )
    return replace(result, findings=tuple(findings))
