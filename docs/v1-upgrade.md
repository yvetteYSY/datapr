# Upgrade and rollback: v0.5 to v1 candidate

DataPR v1.0.0rc1 preserves the documented v0.5 comparison contract. Test the
candidate on a non-critical project in advisory mode before enabling enforcement.

## Python CLI rehearsal

Record the current version and a JSON report:

```bash
datapr --version
datapr compare \
  --base-manifest path/to/base/manifest.json \
  --head-manifest target/manifest.json \
  --format json \
  --out before-v1.json
```

Install the candidate and repeat the same command:

```bash
python -m pip install --force-reinstall \
  https://github.com/yvetteYSY/datapr/releases/download/v1.0.0rc1/datapr-1.0.0rc1-py3-none-any.whl
datapr --version
```

The decision, changes, findings, coverage, and lineage should remain compatible.
`datapr measure` also retains schema 1; its `datapr_version` value intentionally
changes.

Rollback uses the public v0.5 wheel:

```bash
python -m pip install --force-reinstall \
  https://github.com/yvetteYSY/datapr/releases/download/v0.5.0/datapr-0.5.0-py3-none-any.whl
datapr --version
```

## GitHub Action rehearsal

Change only the Action reference and start with advisory enforcement:

```yaml
- uses: yvetteYSY/datapr@v1.0.0rc1
  with:
    base-manifest: .datapr/base/manifest.json
    head-manifest: target/manifest.json
    config: datapr.yml
    enforce: "false"
```

Rollback by restoring `uses: yvetteYSY/datapr@v0.5.0`. Do not use `@main`, and do
not replace the stable `v0` channel with the candidate tag.

## Report a candidate regression

Open a sanitized bug report containing versions, aggregate result differences,
coverage status, and a minimal synthetic reproduction. Do not attach production
manifests, SQL, samples, credentials, paths, or model names.
