# DataPR roadmap

DataPR tracks engineering maturity and production evidence independently. A
version can be stable and publicly useful before enough independent projects exist
to call it production-proven. Claims in documentation must preserve that boundary.

## Shipped foundation: v0.1–v0.4

- dbt artifact and Git-revision comparison
- schema, lineage, SQL-risk, and bounded differential-profile findings
- versioned comparison and privacy-safe measurement contracts
- policy-based terminal, JSON, Markdown, and GitHub Action workflows
- deterministic sampling, resource limits, malformed-input hardening, and a
  50-query dialect corpus
- reproducible scale benchmarks, release pilot, rollback runbook, and synthetic
  acceptance environments

## Now: v0.5 v1 stabilization

### Public contract

- [x] Define the v1 compatibility boundary and exit codes.
- [x] Preserve result schema 1 and measurement schema 1 golden contracts.
- [x] Publish and validate configuration schema 1.
- [x] Keep GitHub Action inputs and outputs backwards-compatible.
- [ ] Complete a v1 release-candidate upgrade rehearsal from v0.5.

### Distribution and release

- [x] Build wheel and source distributions in protected CI.
- [x] Inspect package metadata and install the built wheel before release.
- [x] Automate immutable GitHub release creation and artifact provenance.
- [x] Document public installation from GitHub release assets.
- [ ] Evaluate optional PyPI publication after trusted-publisher ownership is
  configured; PyPI does not block v1.

### Public onboarding

- [x] Provide a realistic dogfood example and three synthetic acceptance paths.
- [x] Document security, resource limits, rollout, rollback, and compatibility.
- [ ] Record a two-minute demo and add an accessible README preview.
- [ ] Run a clean-room v1 release-candidate install using only public docs.

## v1.0 engineering gate

- public contracts are documented and regression-tested;
- package, Action, dialect, synthetic, golden, and resource-limit checks pass;
- a release candidate is built, installed, upgraded, and rolled back through the
  documented process;
- no unresolved critical correctness or security issue is known; and
- v1 release notes accurately state support and limitations.

Independent adopter counts and precision measurements are not version gates.

## Parallel track: production evidence

- recruit three independent design partners;
- measure median end-to-end time to first report;
- review false positives and incomplete coverage with project owners;
- record risky changes caught before merge; and
- publish only privacy-reviewed aggregate evidence.

Meeting this track allows DataPR to describe a release as production-proven. Until
then, releases are described as engineering-stable, fixture-backed, or publicly
available according to the evidence actually collected.

## Later ecosystem work

- OpenLineage import/export after a concrete integration need;
- warehouse-native execution behind an explicit read-only adapter;
- operational guidance for very large manifests and self-hosted runners;
- additional project adapters such as SQLMesh;
- catalog, ownership, and organization-specific policy integrations; and
- optional AI explanations grounded exclusively in emitted evidence.

## Production-evidence targets

| Signal | Target |
| --- | ---: |
| Independent adopter projects | 3 |
| Risky changes caught before merge | 2 |
| Median time to first report | <15 minutes |
| Reviewed high-severity finding precision | ≥90% |
| Dialect fixture queries | ≥50 |
| p95 analysis time at 10,000 models | <30 seconds |

The roadmap changes when correctness, security, or user evidence contradicts an
assumption. Feature requests without a demonstrated review-time use case remain
candidates rather than commitments.
