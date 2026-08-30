# ADR-0002: Profile paired model outputs

- **Status:** Accepted
- **Date:** 2026-08-29

## Context

Executing arbitrary dbt projects requires warehouse credentials, adapter-specific setup, and potentially expensive or destructive operations. That would make the first release difficult to adopt safely.

## Decision

The v0.1 execution boundary accepts paired, pre-materialized model outputs named `<model>.parquet`, `<model>.csv`, or `<model>.json`. DuckDB calculates aggregate differences locally with a configured sample bound. DataPR does not write to a warehouse or emit raw row values.

## Consequences

- The core remains local, read-only, and reproducible.
- Callers control how samples are generated and redacted.
- Setup requires an artifact-generation step outside DataPR.
- Warehouse semantic differences and sampling bias remain visible limitations.
- Warehouse-native execution can be added later behind a read-only adapter without changing the evidence contract.
