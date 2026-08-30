# DataPR

**See the impact of a data change before it reaches production.**

DataPR is an open-source pull-request reviewer for analytics engineering. It compares a proposed SQL or dbt change with its base revision and reports schema breaks, downstream blast radius, data-profile differences, and likely performance regressions.

```text
$ datapr compare main..HEAD

DataPR found 2 high-risk changes

orders.customer_id                 BREAKING
  type: BIGINT -> VARCHAR
  impact: 8 downstream models, 2 critical
  sample: 3.8% fewer rows join to customers

daily_revenue                      PERFORMANCE
  estimated scanned data: +71%
  cause: partition predicate removed
```

> [!IMPORTANT]
> DataPR is currently in the design and prototyping stage. Interfaces described here may change.

## Why DataPR?

Code review shows how SQL text changed. It rarely shows what the change will do to data or downstream consumers. DataPR brings that missing context into the pull request, where teams can act on it before merge.

The project is guided by four principles:

- **Evidence before explanation.** Deterministic analysis finds facts; optional AI can explain them.
- **Useful locally.** The core workflow runs on a laptop and does not require a hosted control plane.
- **Open interfaces.** Lineage, policies, and results use documented formats with OpenLineage interoperability as a goal.
- **Incremental adoption.** A team can start with one dbt project and one CI job.

## MVP

The first release will support:

- dbt manifest ingestion
- changed-model detection from a Git diff
- table- and selected column-level lineage
- schema compatibility checks
- sampled before/after execution with DuckDB
- row-count, null-rate, and distribution comparisons
- Markdown and JSON reports
- policy-based CI exit codes
- a reusable GitHub Action

See [the design document](docs/design.md) for architecture, contracts, tradeoffs, and milestones.

## Proposed workflow

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

## Proposed CLI

```bash
# Compare the current branch with main.
datapr compare main..HEAD

# Write a PR comment and a machine-readable report.
datapr compare main..HEAD \
  --format markdown --out datapr-report.md \
  --json-out datapr-report.json

# Validate project configuration and available inputs.
datapr doctor
```

## What DataPR is not

DataPR is not a data catalog, orchestrator, or production observability platform. It consumes metadata from those systems and focuses on one decision: **is this data change safe to merge?**

## Project status

The immediate objective is a compelling vertical slice: an intentionally dangerous one-line SQL change, analyzed locally and summarized in a pull-request comment.

Near-term milestones:

1. Define the result schema and fixture repository.
2. Detect changed dbt models and downstream impact.
3. Compare schemas and sampled query outputs in DuckDB.
4. Render a useful Markdown report.
5. Package the workflow as a GitHub Action.

## Contributing

Early design feedback is welcome. Useful areas include SQL dialect fixtures, compatibility rules, representative failure cases, and integrations. Until the first executable prototype lands, please start with an issue describing the use case and expected behavior.

## License

Licensed under the [Apache License 2.0](LICENSE).
