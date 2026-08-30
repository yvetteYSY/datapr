# SQL dialect support

DataPR uses the dbt manifest's `metadata.adapter_type` to select a SQLGlot parser dialect. The current fixture matrix verifies common projection lineage for five adapters.

| dbt adapter | Tested constructs | Column lineage | Risk heuristics |
|---|---|---:|---:|
| BigQuery | backtick identifiers, `SAFE_CAST`, `QUALIFY`, window functions | Fixture-backed | Supported |
| Snowflake | `IFF`, `QUALIFY`, window functions | Fixture-backed | Supported |
| Spark | casts and `EXPLODE` projections | Fixture-backed | Supported |
| Postgres | JSON text extraction with `->>` | Fixture-backed | Supported |
| DuckDB | list functions and standard projections | Fixture-backed | Supported |

“Fixture-backed” means the checked-in examples parse and produce expected source-column mappings. It does not imply complete support for every construct in that dialect.

## Degraded behavior

- Missing compiled SQL is listed under `coverage.missing_sql_models`.
- A parse failure is listed under `coverage.sql_parse_failures` and emits a `lineage.sql_parse_incomplete` finding.
- An absent adapter type uses SQLGlot's generic parser.
- Unsupported analysis reduces coverage; it never silently becomes proof of safety.

## Adding a dialect case

Add a compact, representative query and expected mapping to [`tests/fixtures/dialects/cases.json`](../tests/fixtures/dialects/cases.json). Prefer constructs observed in a real project. A fixture should identify the smallest unsupported syntax rather than copy production SQL or sensitive identifiers.

The v0.2 target is at least 50 representative queries across these adapters, with incomplete-coverage and false-positive rates reported alongside the count.
