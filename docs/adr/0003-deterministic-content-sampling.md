# ADR-0003: Use deterministic content-hash sampling

- **Status:** Accepted
- **Date:** 2026-08-30

## Context

The v0.1 profiler bounded work with `LIMIT`, making aggregate evidence depend on physical file order. Random reservoir sampling would reduce ordering bias but make pull-request reports difficult to reproduce. DuckDB's native `hash()` is deterministic within a runtime, but its implementation is explicitly allowed to change between DuckDB versions.

## Decision

DataPR v0.2 orders rows by MD5 of a versioned JSON representation of the shared base/head columns plus a configured seed, then takes the configured row bound. Columns are sorted before the row struct is constructed. Profiling uses one DuckDB thread and materializes each sample once per model pair.

The default strategy is `hash`; `first` remains available for v0.1 compatibility. Reports expose the strategy, seed, and algorithm identifier `md5-json-v1`. MD5 is used only as a stable distribution function, not for security.

## Consequences

- Identical row sets yield identical aggregate samples regardless of file order.
- Base and head use the same shared-column sampling basis when one exists.
- Changing the seed produces a reproducible alternative sample.
- Value changes in sampled columns can change sample membership; evidence remains distributional rather than row-paired.
- Sorting requires a full bounded-input scan and can be more expensive than first-row sampling.
- A future algorithm change requires a new identifier rather than silently changing report semantics.
