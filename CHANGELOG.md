# Changelog

All notable changes to DataPR are documented here. The project uses semantic versioning. v0.5 begins the v1 contract freeze: public interfaces will not intentionally break before v1.0.

## [Unreleased]

## [1.0.0rc1] - 2026-08-30

### Added

- an automated public-wheel upgrade rehearsal from v0.5.0 to the v1 candidate and rollback to v0.5.0, with exact comparison-contract equality checks
- a bounded release-candidate pilot that validates exact-tag Action resolution, expected enforcement evidence, and privacy-safe candidate measurements
- prerelease-aware GitHub publication that marks release-candidate tags without advancing the stable `v0` or future `v1` channels

### Changed

- mark the documented public v1 contract as the `v1.0.0rc1` compatibility candidate
- promote package metadata from alpha to beta while retaining the separate, not-yet-production-proven status

### Fixed

- clarify that exact semantic tags are immutable by project policy while GitHub's repository-level immutable-release enforcement is not enabled

## [0.5.0] - 2026-08-30

### Added

- a manual workflow that pilots the published v0.4.0 Action from a clean checkout and preserves synthetic evidence
- a production rollout, promotion-gate, and rollback runbook for controlled adoption
- three explicitly synthetic BigQuery, Snowflake, and Postgres functional prototypes with independent CI acceptance jobs
- a documented v1 stability, support, exit-code, and compatibility policy
- a versioned configuration JSON schema validated against the example configuration
- automated source/wheel build verification, installation smoke tests, provenance attestation, and GitHub release creation from exact semantic tags

### Fixed

- configuration now fails closed on unknown keys, negative policy thresholds, mistyped booleans, and invalid profile-directory values instead of silently accepting schema-invalid input

### Changed

- separate v1 engineering readiness from post-release production-adoption evidence
- promote package metadata from pre-alpha to alpha and add public project links

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

[Unreleased]: https://github.com/yvetteYSY/datapr/compare/v1.0.0rc1...HEAD
[1.0.0rc1]: https://github.com/yvetteYSY/datapr/releases/tag/v1.0.0rc1
[0.5.0]: https://github.com/yvetteYSY/datapr/releases/tag/v0.5.0
[0.4.0]: https://github.com/yvetteYSY/datapr/releases/tag/v0.4.0
[0.3.0]: https://github.com/yvetteYSY/datapr/releases/tag/v0.3.0
[0.2.0]: https://github.com/yvetteYSY/datapr/releases/tag/v0.2.0
[0.1.0]: https://github.com/yvetteYSY/datapr/releases/tag/v0.1.0
