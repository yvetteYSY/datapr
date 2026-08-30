# DataPR: Initial Design

- **Status:** Draft
- **Audience:** Contributors, adopters, and maintainers
- **Last updated:** 2026-08-29

## 1. Summary

DataPR evaluates the likely impact of a SQL or dbt change before merge. It combines static analysis, lineage, sampled differential execution, and configurable policies to produce review evidence in Markdown and a stable machine-readable result.

The initial product wedge is intentionally narrow:

> Given a base revision and a proposed revision of a dbt project, identify changed models, measure their downstream blast radius, compare their schemas and sampled outputs, and decide whether CI should warn or fail.

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
3. Detect added, removed, renamed, and retyped columns.
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

project:
  type: dbt
  manifest: target/manifest.json

execution:
  engine: duckdb
  sample_rows: 100000

policies:
  fail_on:
    - removed_column
    - incompatible_type_change
  warn_on:
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

### 5.3 Differential execution

DuckDB executes base and proposed models against the same bounded inputs. The engine compares:

- row count and distinctness;
- null rates;
- numeric ranges and quantiles;
- categorical frequencies;
- join-key coverage when keys are configured;
- execution time and scanned-data proxies where available.

Sampling is evidence, not proof. Every metric records sampling strategy, population coverage when known, and caveats.

### 5.4 Evidence model

Analyzers do not directly decide pass or fail. They emit typed findings into a versioned evidence model.

Proposed minimal shape:

```json
{
  "schema_version": "0.1",
  "comparison": {"base": "main", "head": "HEAD"},
  "coverage": {"models_analyzed": 12, "models_total": 12},
  "findings": [
    {
      "id": "schema.incompatible_type_change",
      "severity": "high",
      "model": "orders",
      "column": "customer_id",
      "confidence": 1.0,
      "evidence": {
        "before": "BIGINT",
        "after": "VARCHAR",
        "downstream_models": 8
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

MVP optimization targets developer feedback latency, not warehouse-scale execution:

- analyze only nodes changed between revisions and their relevant graph closure;
- cache parsing by content hash;
- cache normalized manifests by artifact hash;
- cap graph traversal and report truncation explicitly;
- push projection and sampling into DuckDB;
- allow execution to be disabled when only static evidence is available.

Target for the fixture project: a warm static analysis under five seconds and a full sampled comparison under two minutes in CI.

## 8. Privacy and security

- Local execution is the default; no telemetry is required.
- Reports should contain aggregates, not raw row values, unless explicitly enabled.
- Configuration supports column redaction before rendering.
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

### Milestone 0: Contract and demonstration

- Versioned result schema.
- Fixture dbt project with a dangerous one-line change.
- Hand-authored example PR report.
- Architecture decision records for the project IR and evidence/policy split.

### Milestone 1: Static vertical slice

- Load base and head dbt manifests.
- Detect changed models.
- Build table-level lineage.
- Detect schema incompatibilities.
- Render terminal, JSON, and Markdown reports.

### Milestone 2: Differential evidence

- Execute compatible fixtures in DuckDB.
- Compute bounded profile differences.
- Record coverage, sampling, and provenance.
- Add deterministic CI policy evaluation.

### Milestone 3: GitHub adoption path

- Publish a reusable GitHub Action.
- Post or update one PR comment.
- Add example repository and two-minute demo.
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

## 12. Open questions

1. Should the first release require two compiled dbt manifests, or compile each revision itself?
2. What stable identity should a model use across file moves and renames?
3. Which column-lineage constructs are required for the first credible demo?
4. How should samples be made deterministic across engines and revisions?
5. Should a missing or partial execution environment default to `warn` or be policy-controlled?
6. Which parts of the result schema can align directly with OpenLineage facets?

## 13. Initial decisions

- Python is the proposed implementation language for ecosystem accessibility.
- DuckDB is the initial execution engine.
- dbt is the initial project adapter.
- JSON is the canonical output; terminal and Markdown are projections.
- Deterministic findings and policy decisions remain independent of optional AI explanations.
