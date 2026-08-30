# Security policy

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability. Use GitHub's private vulnerability reporting feature for this repository.

Include the affected version, reproduction steps, impact, and any suggested mitigation. Do not include production credentials or sensitive datasets.

## Data-handling expectations

DataPR runs locally or in the caller's CI environment. It does not require a hosted service or telemetry. Differential reports emit aggregates rather than raw values. Users remain responsible for redacting generated artifacts and limiting CI credentials and sample access.

Manifests and profile inputs are treated as untrusted. DataPR rejects malformed structures and applies documented byte, node, SQL, column, model, sample, and DuckDB memory boundaries. These controls are defense in depth rather than an operating-system sandbox; run analysis with least-privilege credentials in an isolated CI workspace. See [resource limits](docs/resource-limits.md).
