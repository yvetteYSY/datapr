# GitHub Action

DataPR can run as a composite action after a workflow produces dbt manifests for the base and proposed revisions.

## Minimal workflow

```yaml
name: DataPR

on:
  pull_request:

permissions:
  contents: read
  pull-requests: write

jobs:
  datapr:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      # Compile or download both artifacts before this step. The exact commands
      # depend on how your project installs dbt and accesses its warehouse.

      - uses: yvetteYSY/datapr@v0
        with:
          base-manifest: .datapr/base/manifest.json
          head-manifest: target/manifest.json
          config: datapr.yml
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

The action creates one Markdown comment and updates that same comment on later pushes. It posts the report before enforcing the decision, so a failed check still explains the evidence.

## Differential profiling

Supply paired directories whose files are named after dbt models:

```yaml
      - uses: yvetteYSY/datapr@v0
        with:
          base-manifest: .datapr/base/manifest.json
          head-manifest: target/manifest.json
          base-data-dir: .datapr/base/data
          head-data-dir: .datapr/head/data
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

DataPR recognizes `<model>.parquet`, `<model>.csv`, and `<model>.json`. Reports contain aggregates only; raw row values are not emitted.

## Inputs

| Input | Required | Purpose |
|---|---:|---|
| `base-manifest` | Yes | Base revision dbt manifest. |
| `head-manifest` | Yes | Proposed revision dbt manifest. |
| `config` | No | DataPR policy and execution configuration. |
| `base-data-dir` | No | Base outputs for local profiling. |
| `head-data-dir` | No | Head outputs for local profiling. |
| `github-token` | No | Creates or updates the PR comment. |
| `enforce` | No | Defaults to `true`; fail when policy decides fail. |

## Security notes

- Give the workflow only `contents: read` and `pull-requests: write`.
- Do not expose warehouse secrets to untrusted fork workflows.
- Generate bounded, redacted samples before invoking DataPR.
- Use `v0` for backwards-compatible v0 updates, `v0.1.0` for an immutable release reference, or a full commit SHA for maximum supply-chain control.
- Fork pull requests may receive a read-only `GITHUB_TOKEN`; DataPR still enforces analysis and emits a workflow report when it cannot write a PR comment.
