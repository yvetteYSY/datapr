"""Map deterministic findings to a merge decision."""

from __future__ import annotations

from dataclasses import replace

from datapr.config import PolicyConfig
from datapr.models import Comparison, DECISION_ORDER, Finding


def _finding_decision(finding: Finding, policy: PolicyConfig) -> str:
    if finding.id in policy.fail_on:
        return "fail"
    if finding.id in policy.warn_on:
        return "warn"
    if (
        finding.id == "lineage.downstream_impact"
        and int(finding.evidence.get("downstream_models", 0))
        >= policy.downstream_models
    ):
        return "warn"
    if (
        finding.id == "profile.row_count_changed"
        and float(finding.evidence.get("change_percent", 0.0))
        >= policy.row_count_change_percent
    ):
        return "warn"
    if (
        finding.id == "profile.null_rate_changed"
        and float(finding.evidence.get("change_percentage_points", 0.0))
        >= policy.null_rate_change_percent
    ):
        return "warn"
    if finding.id == "profile.distribution_changed":
        return "warn"
    return "pass"


def apply_policy(result: Comparison, policy: PolicyConfig) -> Comparison:
    decision = "pass"
    for finding in result.findings:
        candidate = _finding_decision(finding, policy)
        if DECISION_ORDER[candidate] > DECISION_ORDER[decision]:
            decision = candidate
    if policy.fail_on_incomplete_coverage and not result.coverage.get("complete", True):
        decision = "fail"
    return replace(result, decision=decision)
