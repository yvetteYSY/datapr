# DataPR: System Design

- **Status:** v0.1 implemented; v0.2 adopter-validation design active
- **Audience:** Contributors, adopters, and maintainers
- **Last updated:** 2026-08-29

## 1. Summary

DataPR evaluates the likely impact of a SQL or dbt change before merge. It combines static analysis, lineage, sampled differential execution, and configurable policies to produce review evidence in Markdown and a stable machine-readable result.

The initial product wedge is intentionally narrow:

> Given a base revision and a proposed revision of a dbt project, identify changed models, measure their downstream blast radius, compare their schemas and sampled outputs, and decide whether CI should warn or fail.

### 1.1 Implementation status

The v0.1 MVP implements the product wedge end to end:

- dbt manifest normalization and Git-revision artifact loading;
- model, schema, dependency, and downstream-impact comparison;
- selected column-level lineage with SQLGlot;
- inferred performance-risk checks for removed filters, cross joins, and wildcard projections;
- bounded DuckDB profiling of paired CSV, Parquet, or JSON model outputs;
- typed findings with severity, confidence, provenance, and coverage;
- configurable merge decisions and terminal, JSON, and Markdown renderers;
- a reusable GitHub Action that updates one pull-request comment before enforcement.

The code is deliberately an adopter-validation release rather than a production-complete platform. The [roadmap](../ROADMAP.md) defines the evidence required to promote it.

## 2. Problem

Data pipeline changes have effects that are poorly represented by textual diffs:

- a renamed or retyped column breaks distant consumers;
- a join modification silently changes cardinality;
- a removed predicate increases scan cost;
- a semantic change preserves the schema but changes a business metric;
- reviewers lack enough ownership and lineage context to route the change correctly.

Existing catalogs and observability systems usually explain production state after deployment. DataPR focuses on prevention at review time.

## 3. Goals

### 3.1 MVP goals

1. Analyze one dbt project without requiring a hosted service.
2. Compare base and proposed revisions deterministically.
3. Detect added, removed, and retyped columns. Rename inference remains a v0.2 goal.
4. Calculate downstream model impact from dbt metadata and parsed SQL.
5. Compare sampled outputs using DuckDB.
6. Emit human-readable Markdown and versioned JSON.
7. Apply user-configurable severity policies and CI exit codes.
8. Make incomplete evidence explicit through confidence and coverage fields.

### 3.2 Non-goals

- Replacing dbt, a catalog, an orchestrator, or a lineage backend.
- Guaranteeing semantic equivalence for arbitrary SQL.
- Running production-scale datasets locally.
- Using an LLM as the source of truth for safety decisions.
- Supporting every SQL dialect in the first release.
- Hosting customer metadata or query results.

## 4. User experience

The primary interface is a local CLI that is also used by a GitHub Action:

```bash
datapr compare main..HEAD --config datapr.yaml
```

The command produces:

1. a terminal summary;
2. `datapr-report.json`, following a versioned schema;
3. optionally, a Markdown PR comment;
4. an exit code determined by policy.

An initial configuration might look like:

```yaml
version: 1

execution:
  sample_rows: 100000

policies:
  fail_on:
    - schema.removed_column
    - schema.incompatible_type_change
  downstream_models: 10
  row_count_change_percent: 5
```

## 5. Architecture

```text
                    +-------------------+
Git revisions ----> | Project adapter   |
dbt artifacts ----> | (dbt first)       |
                    +---------+---------+
                              |
                    normalized project IR
                              |
             +----------------+----------------+
             |                                 |
             v                                 v
    +------------------+              +------------------+
    | Static analyzer  |              | Execution engine |
    | SQL + schemas    |              | DuckDB + samples |
    +---------+--------+              +---------+--------+
              |                                 |
              +---------------+-----------------+
                              v
                    +-------------------+
                    | Evidence model    |
                    | + lineage graph   |
                    +---------+---------+
                              v
                    +-------------------+
                    | Policy evaluator  |
                    +---------+---------+
                              v
                    +-------------------+
                    | Renderers         |
                    | CLI / JSON / MD   |
                    +-------------------+
```

### 5.1 Project adapter

The adapter converts tool-specific artifacts into a normalized intermediate representation (IR):

- nodes: models, sources, seeds, and exposures;
- schemas: named and typed columns when known;
- edges: declared and inferred dependencies;
- ownership and tags;
- compiled and original SQL;
- materialization and dialect metadata.

dbt is the only MVP adapter. The boundary should be documented early so SQLMesh or orchestrator adapters can be added without changing the analysis core.

### 5.2 Static analyzer

The analyzer compares the two project IRs and produces evidence:

- changed nodes and change categories;
- schema differences;
- dependency additions and removals;
- downstream reachability and critical-node impact;
- column lineage for supported SQL constructs;
- heuristics for expensive changes, such as a removed filter or cross join.

SQL parsing should use a maintained multi-dialect parser rather than regex. Unsupported constructs produce an explicit `unknown` result, not an optimistic pass.

### 5.3 Differential profiling

DuckDB profiles paired, pre-materialized base and proposed model outputs. DataPR recognizes model-named CSV, Parquet, and JSON files and compares:

- row count;
- null rates;
- numeric means and ranges.

DataPR does not yet execute arbitrary dbt models or access a production warehouse. Sampling is evidence, not proof. v0.2 selects a reproducible bounded sample by ordering rows on `md5(seed || versioned JSON row)` over sorted shared columns. Each sample is materialized once, and profiling uses one DuckDB thread to avoid order-sensitive aggregate variation. Every emitted metric records its sample bound, strategy, seed, algorithm, and provenance. The legacy `first` strategy remains explicit. Quantiles, categorical frequency comparison, join-key coverage, and warehouse-native execution remain v0.2 candidates that require adopter evidence.

### 5.4 Evidence model

Analyzers do not directly decide pass or fail. They emit typed findings into a versioned evidence model.

Proposed minimal shape:

```json
{
  "schema_version": "1.0",
  "base_manifest": "main:artifacts/manifest.json",
  "head_manifest": "target/manifest.json",
  "coverage": {"manifest_models_analyzed": 12, "complete": true},
  "findings": [
    {
      "id": "schema.incompatible_type_change",
      "severity": "high",
      "model": "orders",
      "confidence": 1.0,
      "provenance": "derived",
      "evidence": {
        "column": "customer_id",
        "before": "BIGINT",
        "after": "VARCHAR"
      }
    }
  ],
  "decision": "fail"
}
```

Separating evidence from policy enables organizations to use different risk thresholds while sharing analyzers and fixtures.

### 5.5 Policy evaluator

The policy engine maps evidence to `pass`, `warn`, or `fail`. MVP policies are declarative comparisons over typed findings. Arbitrary code execution in policy files is out of scope.

### 5.6 Renderers

Renderers consume only the evidence model. The initial renderers are:

- concise terminal output;
- stable JSON for automation;
- Markdown optimized for a pull-request comment.

Long reports should use a summary-first structure and collapse low-risk details where the target supports it.

## 6. Correctness and trust

Trust is the central design constraint. DataPR must distinguish among:

- **observed:** measured by execution;
- **derived:** deterministically calculated from metadata or parsed SQL;
- **inferred:** based on a documented heuristic;
- **unknown:** insufficient or unsupported evidence.

Findings include provenance and confidence. A parser failure, missing manifest, unavailable sample, or partially built model reduces reported coverage and can itself trigger policy.

Optional LLM functionality may summarize findings or propose a migration, but it cannot create, suppress, or change deterministic findings without being visibly identified as advisory output.

## 7. Performance and scale

The current implementation targets developer feedback latency, not warehouse-scale execution. It already:

- analyzes the union of manifest nodes and profiles changed models only;
- performs downstream traversal in memory;
- bounds column profiling by configured sample rows;
- allows profiling to be omitted when only static evidence is available.

Scale work is measurement-led. The checked-in harness publishes 100, 1,000, and 10,000-model results for a linear graph with one percent changed models. Candidate optimizations include SQL parsing by content hash, normalized-manifest caching, report truncation, and bounded traversal. They should not be implemented until the benchmark or an adopter manifest identifies the bottleneck.

Target for the fixture project: a warm static analysis under five seconds and a full sampled comparison under two minutes in CI.

## 8. Privacy and security

- Local execution is the default; no telemetry is required.
- Reports should contain aggregates, not raw row values, unless explicitly enabled.
- Reports omit raw row values; configurable redaction is planned for v0.2.
- CI documentation will recommend least-privilege, read-only data credentials.
- SQL and project artifacts are untrusted inputs; adapters and execution need resource limits.
- PR comments must avoid secrets present in SQL literals or error messages.

## 9. Extension points

The following interfaces are expected after the vertical slice proves useful:

- project adapters;
- catalog and lineage importers, including OpenLineage;
- SQL dialect capabilities;
- execution engines;
- finding rules;
- policy packs;
- report renderers.

An extension declares its supported schema versions and capabilities. The project will avoid a general plugin runtime until at least two real implementations validate each boundary.

## 10. Delivery plan

### Milestone 0: Contract and demonstration — complete

- Versioned result schema.
- Dangerous-change manifest fixtures.
- Generated example terminal, JSON, and Markdown reports.
- Architecture decisions for evidence/policy separation and paired-output profiling.

### Milestone 1: Static vertical slice — complete

- Load base and head dbt manifests.
- Detect changed models.
- Build table-level lineage.
- Detect schema incompatibilities.
- Render terminal, JSON, and Markdown reports.

### Milestone 2: Differential evidence — complete

- Execute compatible fixtures in DuckDB.
- Compute bounded profile differences.
- Record coverage, sampling, and provenance.
- Add deterministic CI policy evaluation.

### Milestone 3: GitHub adoption path — implementation complete

- Publish a reusable GitHub Action.
- Post or update one PR comment.
- Add realistic dbt example repository and two-minute demo. *(Next-phase work.)*
- Publish contribution guides for rules and dialect fixtures.

## 11. Key risks and mitigations

| Risk | Mitigation |
|---|---|
| False confidence from sampling | Display coverage and sampling provenance; never label sampling as proof. |
| SQL dialect complexity | Capability matrix, fixture suites, explicit unknown states. |
| Too many noisy findings | Typed evidence, configurable policy, summary-first rendering. |
| Scope expands into a catalog | Maintain PR-time merge safety as the product boundary. |
| Local and warehouse results diverge | Document engine semantics and later support warehouse-native execution adapters. |
| Integration surface slows delivery | Keep dbt + DuckDB as the only MVP path. |

## 12. Resolved and open questions

Resolved for v0.1:

1. DataPR consumes two precompiled manifests; compilation remains the caller's responsibility.
2. dbt `unique_id` is the model identity. File moves preserve identity; model renames do not yet.
3. Missing SQL, parse failures, and missing profile pairs reduce explicit coverage.
4. Incomplete coverage is policy-controlled through `fail_on_incomplete_coverage`.

Open for adopter validation:

1. Which dbt compilation workflow is least burdensome across GitHub-hosted and self-hosted CI?
2. Which rename signals are reliable enough to avoid false matches?
3. Which SQL dialect constructs account for most real column-lineage failures?
4. Which stable model keys should optionally replace full shared-row content in deterministic sampling?
5. Which result fields map cleanly to OpenLineage facets without coupling DataPR to one backend?
6. What false-positive rate is acceptable for inferred performance findings?

## 13. Current decisions

- Python is the implementation language for ecosystem accessibility.
- DuckDB is the initial execution engine.
- dbt is the initial project adapter.
- JSON is the canonical output; terminal and Markdown are projections.
- Deterministic findings and policy decisions remain independent of optional AI explanations.

Decision rationale is recorded in [`docs/adr`](adr/).

## 14. v0.2 adopter-validation design

The v0.2 phase optimizes for learning, not feature count. Work is admitted only when it improves one of four signals:

1. **Setup success:** a new adopter can obtain two manifests and a useful report in under 15 minutes.
2. **Finding precision:** high-severity static findings are actionable, with a target precision of at least 90% in curated and adopter fixtures.
3. **Coverage visibility:** unsupported SQL or missing samples are immediately understandable from the report.
4. **Review usefulness:** the PR comment changes a merge, migration, or reviewer-routing decision in a documented case.

### 14.1 Proposed technical increments

- A realistic multi-model dbt demo project and dogfood pull request.
- A dialect capability matrix backed by golden fixtures.
- Rename-candidate findings that remain advisory until precision is measured.
- Deterministic hash sampling and categorical/quantile profiles.
- Benchmarks at 100, 1,000, and 10,000 models with published methodology.
- Versioned `v0` action tag and GitHub release automation.
- An OpenLineage mapping design, gated on one real integration request.

### 14.2 Explicitly deferred

- A hosted UI or metadata service.
- Arbitrary third-party plugins.
- Automatic production-warehouse writes.
- LLM-generated correctness findings.
- Support for non-dbt project adapters before the dbt workflow is validated.

### 14.3 Promotion criteria

DataPR can move from v0.2 validation to broader beta when it has:

- three independent adopter projects;
- two documented incidents or risky changes caught before merge;
- a dialect matrix covering at least 50 representative queries;
- p95 static-analysis latency under 30 seconds for a 10,000-model synthetic manifest;
- no unresolved critical security findings;
- stable result-schema compatibility across two minor releases.

### 14.4 Rename-candidate precision guardrails

Rename analysis is an advisory layer over the existing evidence; it never suppresses a model or column removal and does not change the default merge policy. A model rename candidate requires an identical non-empty artifact fingerprint, an identical declared schema, and a mutual one-to-one match. A column rename candidate requires an identical parsed projection expression, an identical declared type, and a mutual one-to-one match.

Ambiguous matches are skipped and counted in `coverage.rename_analysis`. Parse failures are also exposed there without changing global coverage, because rename analysis is optional and inferred. Candidate findings include their signals, confidence, and `blocking: false` so consumers do not mistake a suggestion for proof.
