# Benchmarks

The manifest-scale benchmark exercises DataPR's static pipeline on synthetic linear dbt graphs containing 100, 1,000, and 10,000 models. One percent of models change in each comparison. The measured pipeline includes manifest comparison, downstream traversal, SQL risk checks, rename analysis, and column lineage for changed models.

Run it from an editable project installation:

```bash
python -m benchmarks.manifest_scale \
  --sizes 100 1000 10000 \
  --warmups 1 \
  --iterations 20 \
  --output benchmarks/results.md
```

The benchmark uses a warmup followed by isolated wall-clock observations. The reported p95 uses the nearest-rank method. Results include runtime versions and non-identifying platform information so contributors can compare changes without treating one machine as universal.

The checked-in [results](results.md) are a regression baseline. They are not a substitute for profiling adopter manifests with realistic SQL complexity and graph topology.

Published-release rollout evidence is recorded separately. The [v0.4.0 maintainer pilot](v0.4.0-pilot.md) verifies immutable-tag resolution and clean-checkout integration mechanics against synthetic fixtures; it is not an independent-adopter benchmark.
