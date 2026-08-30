# Static-analysis benchmark results

Generated: 2026-08-30 17:58 UTC

- Platform: Darwin arm64
- Python: 3.12.13
- DuckDB: 1.5.5
- SQLGlot: 30.17.0
- Scenario: linear dependency graph with 1% changed models
- Pipeline: manifest comparison, SQL risk checks, rename analysis, and column lineage

| Models | Changed | Iterations | Minimum | Median | p95 | Target |
|---:|---:|---:|---:|---:|---:|---:|
| 100 | 1 | 20 | 0.0003s | 0.0004s | 0.0005s | — |
| 1,000 | 10 | 20 | 0.0120s | 0.0122s | 0.0127s | — |
| 10,000 | 100 | 20 | 1.8680s | 1.9181s | 2.0613s | <30.000s |

These synthetic results are a regression baseline, not a promise for every project. Manifest shape, SQL complexity, hardware, and changed-model ratio materially affect runtime.
