# SQL dialect support

DataPR uses the dbt manifest's `metadata.adapter_type` to select a SQLGlot parser dialect. The current fixture matrix verifies 50 representative projection-lineage queries across five adapters.

| dbt adapter | Cases | Tested constructs | Expected lineage |
|---|---|---:|---:|
| BigQuery | 10 | backticks, `SAFE_CAST`, `QUALIFY`, arrays, dates, regex, CTEs, windows | 10/10 exact |
| Snowflake | 10 | `IFF`, `QUALIFY`, objects, `LISTAGG`, dates, regex, CTEs, windows | 10/10 exact |
| Spark | 10 | casts, `EXPLODE`, arrays, JSON, dates, regex, CTEs, windows | 10/10 exact |
| Postgres | 10 | JSON operators, arrays, dates, regex, CTEs, windows | 10/10 exact |
| DuckDB | 10 | lists, JSON, dates, regex, CTEs, windows | 10/10 exact |

“Fixture-backed” means the checked-in examples parse and produce expected source-column mappings. It does not imply complete support for every construct in that dialect.

## Degraded behavior

- Missing compiled SQL is listed under `coverage.missing_sql_models`.
- A parse failure is listed under `coverage.sql_parse_failures` and emits a `lineage.sql_parse_incomplete` finding.
- An absent adapter type uses SQLGlot's generic parser.
- Unsupported analysis reduces coverage; it never silently becomes proof of safety.

## Adding a dialect case

Add a compact, representative query and expected mapping to [`tests/fixtures/dialects/cases.json`](../tests/fixtures/dialects/cases.json). Prefer constructs observed in a real project. A fixture should identify the smallest unsupported syntax rather than copy production SQL or sensitive identifiers.

The v0.3 corpus contains 50/50 parsing successes and 50/50 exact expected mappings. This is curated compatibility evidence, not a production precision estimate. False-positive and incomplete-coverage rates still require adopter manifests.
