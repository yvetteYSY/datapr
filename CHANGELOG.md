# Changelog

All notable changes to DataPR are documented here. The project uses semantic versioning before 1.0: minor versions may evolve public interfaces, while patch versions remain backwards-compatible.

## [Unreleased]

### Added

- a manual workflow that pilots the published v0.4.0 Action from a clean checkout and preserves synthetic evidence
- a production rollout, promotion-gate, and rollback runbook for controlled adoption

## [0.4.0] - 2026-08-30

### Added

- a privacy-safe `datapr measure` command for local analysis-time, finding-count, decision, and coverage aggregates
- a versioned measurement schema, adopter-validation protocol, and privacy-aware issue and pull-request templates
- a synthetic golden measurement example and exact contract-regression test contributed through the newcomer queue

## [0.3.0] - 2026-08-30

### Added

- a 50-query dialect corpus with ten exact lineage cases each for BigQuery, Snowflake, Spark, Postgres, and DuckDB
- fail-closed manifest limits for bytes, nodes, columns, SQL length, nesting, and malformed structures
- configurable profiling limits for samples, models, file bytes, columns, and DuckDB memory
- resource-limit coverage metadata, stress tests, security guidance, and architecture decisions

## [0.2.0] - 2026-08-30

### Added

- conservative, non-blocking model rename candidates based on unique artifact fingerprints and declared schemas
- conservative column rename candidates based on parsed projection expressions and declared types
- rename-analysis coverage that records skipped ambiguity and parse failures
- deterministic, input-order-independent content-hash sampling with a configurable seed
- a legacy `first` sampling strategy for explicit v0.1 compatibility
- reproducible 100, 1,000, and 10,000-model static-analysis benchmarks

### Fixed

- differential profiling preserves an existing incomplete-coverage result instead of replacing it when all configured sample pairs are present

## [0.1.0] - 2026-08-29

### Added

- dbt manifest comparison from explicit paths or Git revisions
- model, schema, dependency, and downstream-impact findings
- selected column-level lineage through SQLGlot
- fixture-backed BigQuery, Snowflake, Spark, Postgres, and DuckDB parsing
- inferred removed-filter, cross-join, and wildcard-projection risks
- bounded DuckDB comparison of paired CSV, Parquet, and JSON model outputs
- row-count, null-rate, and numeric-distribution findings
- configurable `pass`, `warn`, and `fail` policies
- terminal, JSON, and Markdown reports with explicit provenance and coverage
- versioned result schema `1.0`
- reusable composite GitHub Action with update-in-place PR comments
- realistic dogfood project and intentionally blocked demonstration PR
- protected `main`, Python 3.10–3.12 CI, action smoke tests, and golden reports

### Security

- PR comment failures caused by read-only fork tokens degrade to workflow warnings; deterministic analysis and policy enforcement continue.
- Reports contain aggregate evidence rather than raw row values.

### Known limitations

- callers must produce both dbt manifests;
- column lineage covers selected projections rather than every dialect construct;
- differential profiling consumes pre-materialized local outputs;
- sampling uses a bounded first-row strategy in v0.1;
- the Python package is not yet published to PyPI.

[Unreleased]: https://github.com/yvetteYSY/datapr/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/yvetteYSY/datapr/releases/tag/v0.4.0
[0.3.0]: https://github.com/yvetteYSY/datapr/releases/tag/v0.3.0
[0.2.0]: https://github.com/yvetteYSY/datapr/releases/tag/v0.2.0
[0.1.0]: https://github.com/yvetteYSY/datapr/releases/tag/v0.1.0
