# Production rollout

DataPR v0.5.0 is the public v1-stabilization release. The immutable `v0.5.0` tag
and movable compatible `v0` tag are promoted by engineering gates. Independent
adoption evidence determines whether the project is described as
production-proven; it does not block public versioning.

## Rollout sequence

1. Pin `yvetteYSY/datapr@v0.5.0` or the full verified commit SHA. Do not use
   `@main`.
2. Start in advisory mode with `enforce: "false"` on a non-critical dbt project.
3. Generate both base and head manifests with the same dbt and adapter versions.
4. Keep profiling disabled initially, or provide only bounded and redacted local
   samples.
5. Review every high- and critical-severity finding with a project owner.
6. Run `datapr measure` and record end-to-end time separately using the
   [adopter-validation protocol](adopter-validation.md).
7. Enable enforcement first for deterministic model removal, column removal, and
   incompatible type changes.
8. Keep inferred SQL risks, profiling drift, and rename candidates advisory until
   project-specific precision is known.

## Release promotion gates

An immutable release and its compatible major tag may be published when:

- the tagged commit is contained in protected `main`;
- required Python, Action, package, schema, and functional-acceptance checks pass;
- the package version, tag, changelog, and release notes agree;
- the source distribution and wheel build, install, and execute successfully;
- build provenance is generated and artifacts are attached to the release; and
- the published-tag pilot resolves the release and produces a valid report.

These gates prove release mechanics and engineered behavior, not production
precision.

## Production-evidence status

The project may be described as production-proven only after:

- three independent projects complete a pilot;
- median end-to-end time to first report is below 15 minutes;
- at least two risky changes are caught before merge;
- assessed high-severity precision is at least 90%, with the reviewed denominator
  reported;
- incomplete coverage is understood and not silently treated as safety; and
- no credential, raw-value, or proprietary-identifier exposure is found.

Until those signals exist, use “public v1 stabilization,” “fixture-backed,” or
“engineering-ready,” not “production-proven.”

## Production controls

- Grant only `contents: read` and `pull-requests: write` when comments are needed.
- Do not expose warehouse credentials to untrusted fork workflows.
- Keep protected branches and required CI checks enabled.
- Pin an immutable tag or commit for regulated or high-assurance repositories.
- Retain aggregate reports according to the repository's data-classification
  policy.
- Assign an owner for policy changes, false-positive review, and upgrades.

## Rollback

If v0.5.0 causes unexpected failures:

1. change the workflow reference back to `yvetteYSY/datapr@v0.4.0`;
2. set `enforce: "false"` if reports are useful but enforcement is noisy;
3. preserve a synthetic reproduction and privacy-reviewed aggregate measurement;
4. open a sanitized bug report using the repository issue form; and
5. do not move or delete immutable release tags.

The movable `v0` tag is a convenience channel, not a rollback guarantee.
Production repositories should pin the exact version they tested.

## Maintainer pilot

The manual [`Published release pilot`](../.github/workflows/release-pilot.yml)
starts its timer before checkout, invokes the public v0.5.0 Action against
synthetic fixtures, verifies the expected policy result, generates a privacy-safe
measurement, and preserves both artifacts for 14 days. It proves release
resolution and integration mechanics; it does not count as an independent adopter
or production-precision evidence.

The historical [v0.4.0 pilot](../benchmarks/v0.4.0-pilot.md) passed in a ten-second
GitHub-hosted job. Checkout through verified report took no more than six seconds,
while DataPR analysis took 0.001673 seconds with complete coverage and the expected
failing decision.
