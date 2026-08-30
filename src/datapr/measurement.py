"""Privacy-safe aggregate measurements for adopter validation."""

from __future__ import annotations

from collections import Counter
import json
from typing import Any

from datapr import __version__
from datapr.models import Comparison


def _count_items(value: Any) -> int:
    return len(value) if isinstance(value, (list, tuple, set, frozenset)) else 0


def build_measurement(
    result: Comparison, analysis_seconds: float
) -> dict[str, Any]:
    """Summarize a comparison without paths, model names, SQL, or raw values."""
    severity_counts = Counter(finding.severity for finding in result.findings)
    provenance_counts = Counter(finding.provenance for finding in result.findings)
    finding_counts = Counter(finding.id for finding in result.findings)
    coverage = result.coverage
    rename = coverage.get("rename_analysis")
    rename = rename if isinstance(rename, dict) else {}
    return {
        "measurement_schema_version": "1.0",
        "datapr_version": __version__,
        "analysis_seconds": round(max(analysis_seconds, 0.0), 6),
        "decision": result.decision,
        "models": {
            "base": result.models_base,
            "head": result.models_head,
            "changed": len(result.changes),
        },
        "findings": {
            "total": len(result.findings),
            "by_severity": dict(sorted(severity_counts.items())),
            "by_provenance": dict(sorted(provenance_counts.items())),
            "by_id": dict(sorted(finding_counts.items())),
        },
        "coverage": {
            "complete": bool(coverage.get("complete", True)),
            "manifest_models_analyzed": int(
                coverage.get("manifest_models_analyzed", 0)
            ),
            "static_lineage": bool(coverage.get("static_lineage", False)),
            "column_lineage_models": int(coverage.get("column_lineage_models", 0)),
            "missing_sql_model_count": _count_items(
                coverage.get("missing_sql_models")
            ),
            "sql_parse_failure_count": _count_items(
                coverage.get("sql_parse_failures")
            ),
            "differential_execution": bool(
                coverage.get("differential_execution", False)
            ),
            "profiled_models": int(coverage.get("profiled_models", 0)),
            "missing_profile_model_count": _count_items(
                coverage.get("missing_profile_models")
            ),
            "rename_analysis": {
                "complete": bool(rename.get("complete", True)),
                "models_evaluated": int(rename.get("models_evaluated", 0)),
                "parse_failure_count": _count_items(rename.get("parse_failures")),
                "candidates": int(rename.get("candidates", 0)),
                "ambiguous_pairs_skipped": int(
                    rename.get("ambiguous_pairs_skipped", 0)
                ),
            },
        },
    }


def render_measurement(result: Comparison, analysis_seconds: float) -> str:
    return json.dumps(build_measurement(result, analysis_seconds), indent=2)
