# Synthetic design-partner prototypes

These three fictional environments are executable acceptance fixtures for DataPR.
They are **not customers, testimonials, pilots, or evidence of external adoption**.
Their purpose is to exercise realistic workflows before asking real design partners to
connect private projects.

| Prototype | Adapter | Functional path | Expected decision |
| --- | --- | --- | --- |
| `commerce_bigquery` | BigQuery | breaking schema and downstream impact | fail |
| `fintech_snowflake` | Snowflake | SQL cost-risk policy | fail |
| `saas_postgres` | Postgres | bounded differential profiling | warn |

Run all prototypes from the repository root:

```bash
python examples/synthetic_partners/run.py
```

Run one and retain its reports:

```bash
python examples/synthetic_partners/run.py \
  --partner saas_postgres \
  --out-dir .datapr/synthetic-partners
```

For every prototype the runner:

1. validates both manifests with `datapr doctor`;
2. creates a JSON comparison with policy enforcement;
3. creates a privacy-safe aggregate with `datapr measure`;
4. checks the expected decision and required finding IDs; and
5. confirms the aggregate does not contain fixture model names.

The default output directory is temporary and removed after the run. Pass
`--out-dir` to retain reports locally. Generated reports are intentionally ignored
by Git.

See [the functional-test protocol](../../docs/synthetic-partner-prototypes.md) for
scope, limitations, and how to translate these simulations into real pilots.
