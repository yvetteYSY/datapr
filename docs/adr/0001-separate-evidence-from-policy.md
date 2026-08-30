# ADR-0001: Separate evidence from policy

- **Status:** Accepted
- **Date:** 2026-08-29

## Context

The same data change can be blocking for one organization and informational for another. If analyzers directly choose CI outcomes, reusable correctness logic becomes coupled to local risk tolerance.

## Decision

Analyzers emit versioned, typed findings with severity, confidence, provenance, and evidence. A separate policy evaluator maps those findings and coverage to `pass`, `warn`, or `fail`. Renderers consume the resulting comparison without reinterpreting evidence.

## Consequences

- Organizations can share analyzers while configuring different thresholds.
- JSON remains the canonical automation contract.
- Finding identifiers require compatibility discipline.
- Policy cannot silently suppress the underlying evidence in reports.
