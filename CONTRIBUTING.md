# Contributing to DataPR

Thank you for helping make data changes safer to review.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --editable .
python -m unittest discover -s tests -v
```

## Good first contributions

- Add a SQL dialect fixture with the expected column-lineage mapping.
- Add a realistic dbt manifest compatibility case.
- Add a profiling input pair that captures a common data incident.
- Improve a finding message without changing its evidence.

## Design rules

1. Deterministic analysis creates findings; AI may explain but never silently alter them.
2. Unsupported analysis reports incomplete coverage instead of passing optimistically.
3. Reports contain aggregate evidence, not raw data values, by default.
4. New integrations begin with fixtures and a documented capability boundary.
5. Keep the product focused on the pre-merge decision.

## Pull requests

Keep changes focused, add tests for behavior, and update the result schema or documentation when a public contract changes. Run the full test suite and `git diff --check` before opening a pull request.

Use the structured issue forms for bugs, evidence-backed feature proposals, and adopter validation. Pull requests should complete the privacy and result-contract checklist. Never include credentials, production manifests, compiled proprietary SQL, or warehouse samples; reduce reproductions to synthetic fixtures.
