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

## Compatibility

Within major schema version 1, fields may be added but existing meanings will not change. Consumers should ignore unknown fields. A future breaking contract will use a new schema file and major `schema_version`.
