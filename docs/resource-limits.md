# Resource limits and untrusted inputs

DataPR treats manifests, compiled SQL, and profile files as untrusted input. Limits fail the command with exit code 2; DataPR does not silently skip oversized evidence or convert it into a clean decision.

## Manifest limits

Manifest limits are fixed safety boundaries applied before and during normalization:

| Boundary | Default |
|---|---:|
| UTF-8 JSON bytes | 100 MiB |
| dbt nodes | 100,000 |
| columns per model | 10,000 |
| compiled SQL characters per model | 10,000,000 |

The loader checks a file's size before reading it, and Git-revision inputs are preflighted with their Git object size before `git show` loads the contents. It rejects excessive nesting as invalid JSON and validates model columns, dependencies, metadata, and SQL types before analysis. Library callers can provide a narrower `ManifestLimits` instance.

## Profiling limits

Profiling boundaries are configurable under `execution`:

```yaml
version: 1
execution:
  sample_rows: 100000
  max_sample_rows: 1000000
  max_profile_models: 100
  max_profile_file_bytes: 1073741824
  max_profile_columns: 1000
  memory_limit_mb: 512
```

DataPR checks file sizes and the number of profile-eligible models before opening inputs, checks inferred column counts before sampling, and applies DuckDB's memory limit with one execution thread. Raising a boundary should be an explicit self-hosted-runner decision backed by representative measurements.

## Residual risks

- These controls bound common accidental and adversarial inputs; they are not an operating-system sandbox.
- SQL parsing has byte and character bounds but no independent wall-clock timeout yet.
- Compressed inputs can expand beyond their on-disk size within DuckDB's memory boundary.
- Files can change between the metadata check and DuckDB opening them; trusted CI workspaces remain the recommended execution environment.
- Warehouse-native execution is not part of this boundary.
