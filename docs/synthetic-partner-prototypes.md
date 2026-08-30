# Synthetic design-partner functional tests

## Purpose

The checked-in prototypes provide realistic, repeatable acceptance tests across
three common analytics-engineering environments. They let maintainers verify that
DataPR's core workflows behave coherently before connecting a real repository.

They are deliberately labeled synthetic. A passing run proves fixture-backed
functionality; it does not prove real-world adoption, operational fit, or user
satisfaction and must not be counted toward the v0 production-promotion gates.

## Acceptance matrix

| Archetype | Adapter parser | Input | Functional acceptance |
| --- | --- | --- | --- |
| Commerce | BigQuery | two dbt manifests | fail a removed column and incompatible type; expose downstream impact |
| Fintech | Snowflake | two dbt manifests plus strict policy | fail a removed filter, new cross join, and wildcard projection |
| SaaS | Postgres | two manifests plus paired CSV samples | warn on row-count, null-rate, and numeric distribution drift |

All source data is small, fictional, and safe to commit. `datapr measure` output is
also checked for fixture model-name leakage.

## Run protocol

From a development checkout:

```bash
python -m pip install --editable .
python examples/synthetic_partners/run.py \
  --out-dir .datapr/synthetic-partners
```

Success means all expected decisions and required finding IDs were observed. The
command exits nonzero for a missing finding, an unexpected decision, a privacy
marker in the aggregate, or a CLI/runtime failure. CI runs each archetype as an
independent matrix job so one adapter path cannot mask another.

## Boundary with external validation

These fixtures can support a design-partner demo and help debug onboarding. A real
pilot still requires an independent team to run DataPR on its own project and
review the usefulness, noise, runtime, coverage, and rollback experience. Record
only real pilot evidence under the adopter-validation protocol.

When adapting a fixture for a real team:

1. start in advisory mode with the immutable release tag;
2. replace manifests and optional samples locally without committing private data;
3. tune policy thresholds with the team;
4. share only the privacy-safe measurement after their review; and
5. record feedback and promotion evidence separately from these simulations.
