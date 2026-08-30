# Adopter validation protocol

DataPR v0.4 adds a local, privacy-safe measurement path for learning from real pull-request workflows without collecting telemetry. DataPR never uploads this output. Adopters choose whether to share the aggregate file or copy selected counts into an issue.

## Generate a measurement

Run the same inputs used for a normal comparison:

```bash
datapr measure \
  --base-manifest .datapr/base/manifest.json \
  --head-manifest target/manifest.json \
  --config datapr.yml \
  --out datapr-measurement.json
```

Git-revision mode and optional profile directories are also supported:

```bash
datapr measure main..HEAD \
  --manifest-path target/manifest.json \
  --base-data-dir .datapr/base/data \
  --head-data-dir .datapr/head/data
```

The output follows [`measurement-v1.schema.json`](../schemas/measurement-v1.schema.json). It contains analysis duration, model and finding counts, decision, and coverage counts. It excludes manifest paths, repository names, model and column names, SQL, finding messages and evidence, raw values, and profile file names.

Review the JSON before sharing it. Finding IDs are included because they are product-level categories such as `schema.removed_column`; organizations with sensitive internal policy identifiers should redact those keys.

## Measure time to first report

`analysis_seconds` measures DataPR from configuration and artifact loading through the final policy decision. For the roadmap's end-to-end time-to-first-report measure:

1. Start from the point where an engineer begins integrating DataPR into a clean checkout.
2. Stop when the first understandable report appears in a pull request or terminal.
3. Record the wall-clock minutes separately from `analysis_seconds`.
4. Note whether manifests and optional samples already existed; artifact generation time is not DataPR analysis time.

This separation prevents installation and dbt-build friction from being mistaken for analyzer performance while preserving the actual adoption experience.

## Measure precision and incomplete coverage

Have a project owner review high- and critical-severity findings and record only aggregate labels:

- high-severity findings reviewed;
- findings judged actionable or correct;
- findings judged false positive;
- findings that could not be assessed;
- pull requests where `coverage.complete` was false;
- the corresponding parse, missing-SQL, and missing-profile counts from the measurement.

Precision is `actionable or correct / assessed findings`. Do not count unassessed findings in the denominator. Report the number reviewed with every percentage; a perfect score on one finding is not reliable evidence.

## Share feedback

Use the repository's **Adopter validation** issue form. Attachments are optional. Never upload manifests, compiled SQL, warehouse samples, credentials, or proprietary identifiers. Aggregate results are useful even when the underlying project must remain private.
