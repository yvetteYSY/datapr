# Result format

JSON is DataPR's canonical output. Terminal and Markdown reports are projections of the same result.

The current contract is [`schemas/result-v1.schema.json`](../schemas/result-v1.schema.json). Its `schema_version` is `1.0`.

## Trust model

Every finding declares its provenance:

- `observed`: measured by DuckDB execution;
- `derived`: deterministically calculated from dbt metadata or parsed SQL;
- `inferred`: a documented heuristic, such as a removed filter;
- `unknown`: evidence is unavailable or unsupported.

`confidence` describes confidence in the finding, not the likelihood of an incident. Coverage is explicit and becomes incomplete when SQL is unavailable, parsing fails, or a configured model-output pair is missing.

## Advisory rename findings

`rename.model_candidate` and `rename.column_candidate` are inferred, non-blocking hints. They carry `blocking: false` plus the exact matching signals in `evidence`. They do not suppress `model.removed` or `schema.removed_column`, so a candidate cannot turn an unsafe migration into a pass.

`coverage.rename_analysis` reports how many relevant models were evaluated, parsing failures, emitted candidates, and ambiguous matches that were intentionally skipped. Rename-analysis incompleteness does not change global coverage because the feature is optional advice rather than proof of compatibility.

## Compatibility

Within major schema version 1, fields may be added but existing meanings will not change. Consumers should ignore unknown fields. A future breaking contract will use a new schema file and major `schema_version`.
