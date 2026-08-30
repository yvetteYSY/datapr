# DataPR

[![CI](https://github.com/yvetteYSY/datapr/actions/workflows/ci.yml/badge.svg)](https://github.com/yvetteYSY/datapr/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

**See the impact of a data change before it reaches production.**

DataPR is an open-source pull-request reviewer for analytics engineering. It compares a proposed SQL or dbt change with its base revision and reports schema breaks, downstream blast radius, data-profile differences, and likely performance regressions.

```text
$ datapr compare --base-manifest base/manifest.json --head-manifest target/manifest.json
DataPR decision: FAIL
Compared 3 base models with 3 head models.
Changed models: 1 | Findings: 4

orders  MODIFIED
  downstream (1): daily_revenue
  column customer_id: type_changed (bigint -> varchar)
  column order_status: added (- -> varchar)
```

> [!IMPORTANT]
> DataPR v0.2 is an adopter-validation release. It is usable on real dbt artifacts, but pre-1.0 interfaces may evolve from adopter feedback.

## Why DataPR?

Code review shows how SQL text changed. It rarely shows what the change will do to data or downstream consumers. DataPR brings that missing context into the pull request, where teams can act on it before merge.

The project is guided by four principles:

- **Evidence before explanation.** Deterministic analysis finds facts; optional AI can explain them.
- **Useful locally.** The core workflow runs on a laptop and does not require a hosted control plane.
- **Open interfaces.** Lineage, policies, and results use documented formats with OpenLineage interoperability as a goal.
- **Incremental adoption.** A team can start with one dbt project and one CI job.

## MVP capabilities

The first release supports:

- dbt manifest ingestion
- changed-model detection from a Git diff
- table- and selected column-level lineage
- schema compatibility checks
- conservative, advisory model and column rename candidates
- sampled before/after execution with DuckDB
- row-count, null-rate, and distribution comparisons
- Markdown and JSON reports
- policy-based CI exit codes
- a reusable GitHub Action

See the [system design](docs/design.md) for architecture and tradeoffs, and the [roadmap](ROADMAP.md) for the evidence-driven continuation plan.

Common projection lineage is fixture-backed for BigQuery, Snowflake, Spark, Postgres, and DuckDB. See the [dialect capability matrix](docs/dialect-support.md) for tested constructs and degraded behavior.

## How it works

```text
Git diff + dbt manifests
          |
          v
   Change analyzer --------> Lineage graph
          |                       |
          v                       v
 DuckDB differential run --> Policy engine
                                  |
                                  v
                       Markdown / JSON / CI result
```

## Quick start

```bash
python -m pip install --editable .

# Validate an artifact.
datapr doctor target/manifest.json

# Compare artifacts compiled from base and head revisions.
datapr compare \
  --base-manifest path/to/base/manifest.json \
  --head-manifest target/manifest.json \
  --format json
```

Try the checked-in dangerous-change fixture:

```bash
datapr compare \
  --base-manifest tests/fixtures/base_manifest.json \
  --head-manifest tests/fixtures/head_manifest.json
```

Compare a tracked manifest across Git revisions:

```bash
datapr compare main..HEAD --manifest-path artifacts/manifest.json
```

Generate a merge-enforced Markdown report:

```bash
datapr compare \
  --base-manifest path/to/base/manifest.json \
  --head-manifest target/manifest.json \
  --config datapr.yml \
  --format markdown \
  --out datapr-report.md \
  --enforce
```

For sampled data comparison, add `--base-data-dir` and `--head-data-dir`. Each directory can contain `<model>.parquet`, `<model>.csv`, or `<model>.json` files. DataPR measures row counts, null rates, and numeric distributions with DuckDB. v0.2 defaults to reproducible content-hash sampling; configure `execution.sample_strategy: first` only when v0.1's file-order behavior is required. The report records the strategy, seed, and versioned hash algorithm.

## GitHub Action

```yaml
- uses: yvetteYSY/datapr@v0
  with:
    base-manifest: .datapr/base/manifest.json
    head-manifest: target/manifest.json
    config: datapr.yml
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

The action posts or updates one PR comment, then enforces the configured decision. See the [complete GitHub Action guide](docs/github-action.md).

Use the movable `v0` tag for backwards-compatible v0 updates, the exact `v0.2.0` release for reproducibility, or a full commit SHA for maximum supply-chain control.

## Dogfood example

[`examples/shop_analytics`](examples/shop_analytics) is a realistic, inspectable dbt-style project with a tracked manifest and bounded model output. The repository runs DataPR against this example on pull requests, extracting the comparison baseline directly from the target commit. See the [example walkthrough](examples/shop_analytics/README.md).

## Finding trust

Every finding is labeled `observed`, `derived`, or `inferred`, with a confidence value and explicit analysis coverage. Missing SQL, unsupported parsing, or absent sample pairs cannot silently become a clean result. See the [versioned result format](docs/result-format.md).

Rename candidates are deliberately advisory. DataPR emits them only for unambiguous pairs supported by identical model fingerprints and schemas, or by identical parsed projection expressions and declared types. It continues to report the underlying removal as breaking until teams confirm the migration is safe.

Untrusted artifacts fail closed against documented manifest and profiling limits. See [resource limits](docs/resource-limits.md) for defaults, configuration, and residual risks. SQL compatibility is backed by a [50-query dialect corpus](docs/dialect-support.md).

## What DataPR is not

DataPR is not a data catalog, orchestrator, or production observability platform. It consumes metadata from those systems and focuses on one decision: **is this data change safe to merge?**

## Project status

The v0.1 MVP is complete, v0.2 adds reproducible evidence, and v0.3 trust hardening is active. Progress and promotion criteria are tracked in the [roadmap](ROADMAP.md); technical decisions are detailed in the [system design](docs/design.md).

Published synthetic scale results and reproduction instructions are available in [`benchmarks`](benchmarks/README.md).

## Contributing

Design feedback and fixtures are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, design rules, and useful first contributions.

All changes to protected `main` go through pull requests and the required test matrix. See [repository governance](docs/governance.md).

## License

Licensed under the [Apache License 2.0](LICENSE).
