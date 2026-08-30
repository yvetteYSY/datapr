# DataPR Roadmap

This roadmap prioritizes evidence that DataPR is useful in real pull-request workflows. Dates are intentionally absent; phase gates are based on outcomes rather than activity.

## Shipped: v0.1 MVP

- dbt artifact and Git-revision comparison
- schema and downstream-impact findings
- selected column-level lineage
- inferred SQL performance risks
- bounded DuckDB differential profiling
- configurable merge policies
- terminal, JSON, and Markdown output
- reusable GitHub Action with update-in-place PR comments
- versioned result schema and explicit coverage

## Now: v0.2 adopter validation

### Dogfood workflow

- [x] Build a realistic dbt demo with a safe baseline.
- [x] Exercise DataPR on a real pull request containing multiple dangerous changes ([PR #1](https://github.com/yvetteYSY/datapr/pull/1)).
- [x] Preserve the generated report as a [golden fixture](examples/shop_analytics/golden/dangerous-change.md).
- Measure time-to-first-report from a clean checkout.

### Correctness and compatibility

- [x] Add an initial dialect matrix for BigQuery, Snowflake, Spark, Postgres, and DuckDB SQL.
- [x] Add golden tests for Markdown and JSON rendering.
- [x] Grow the dialect matrix from 5 to 50 representative queries.
- [x] Add conservative model and column rename candidates as non-blocking, inferred findings.
- Measure false-positive and incomplete-coverage rates.

### Performance and reliability

- [x] Publish reproducible benchmarks for 100, 1,000, and 10,000-model manifests.
- [x] Add deterministic content-hash sampling before expanding distribution metrics.
- [x] Add resource limits and malformed-artifact stress tests.

### Release and adoption

- [x] Create a `v0.1.0` GitHub release and movable `v0` action tag.
- Record a two-minute demo and add an animated README preview.
- Add issue and pull-request templates plus labeled good-first issues.
- Recruit three independent design partners.

## Next: beta readiness

- Validate compatibility across two minor releases of the result schema.
- Add OpenLineage import/export only after a concrete adopter request.
- Add warehouse-native execution behind an explicit read-only adapter.
- Publish operational guidance for large manifests and self-hosted runners.
- Evaluate a PyPI release after package naming and release ownership are settled.

## Later: ecosystem expansion

- Additional project adapters such as SQLMesh.
- Catalog and ownership connectors.
- Organization-specific policy packs.
- Optional advisory AI explanations grounded exclusively in emitted evidence.

## Success measures

| Signal | v0.2 target |
|---|---:|
| Independent adopter projects | 3 |
| Risky changes caught before merge | 2 |
| Median time to first report | <15 minutes |
| High-severity finding precision | ≥90% |
| Dialect fixture queries | ≥50 |
| p95 analysis time at 10,000 models | <30 seconds |

The roadmap will change when adopter evidence contradicts an assumption. Feature requests without a demonstrated review-time use case remain candidates, not commitments.
