# Production rollout

DataPR v0.4.0 is in controlled rollout. The immutable `v0.4.0` tag is published; the movable `v0` tag remains on v0.3.0 until pilot evidence meets the gates below.

## Pilot sequence

1. Pin `yvetteYSY/datapr@v0.4.0` or the full verified commit SHA. Do not use `@main`.
2. Start in advisory mode with `enforce: "false"` on a non-critical dbt repository.
3. Generate both base and head manifests with the same dbt and adapter versions.
4. Keep profiling disabled initially, or provide only bounded and redacted local samples.
5. Review every high- and critical-severity finding with a project owner.
6. Run `datapr measure` and record end-to-end time separately using the [adopter-validation protocol](adopter-validation.md).
7. Enable enforcement only for deterministic model removal, column removal, and incompatible type changes.
8. Keep inferred SQL risks, profiling drift, and rename candidates advisory until project-specific precision is known.

## Promotion gates

Move the compatible `v0` tag to v0.4.0 only after:

- three independent projects complete a pilot;
- median end-to-end time to first report is below 15 minutes;
- at least two risky changes are caught before merge;
- assessed high-severity precision is at least 90%, with the reviewed count reported;
- incomplete coverage is understood and not silently treated as safety;
- no credential, raw-value, or proprietary-identifier exposure is found;
- the published-tag pilot workflow resolves the release and produces a valid report.

## Production controls

- Grant only `contents: read` and `pull-requests: write` when comments are required.
- Do not expose warehouse credentials to untrusted fork workflows.
- Keep protected branches and required CI checks enabled.
- Pin an immutable tag or commit for regulated or high-assurance repositories.
- Retain aggregate reports according to the repository's data-classification policy.
- Assign an owner for policy changes, false-positive review, and upgrade decisions.

## Rollback

If v0.4.0 causes unexpected failures:

1. change the workflow reference back to `yvetteYSY/datapr@v0.3.0`;
2. set `enforce: "false"` if reports are useful but policy enforcement is noisy;
3. preserve the failing synthetic reproduction and aggregate measurement;
4. open a sanitized bug report using the repository issue form;
5. do not move or delete immutable release tags.

The movable `v0` tag provides no rollback guarantee by itself. Production repositories should pin the exact tested version.

## Maintainer pilot

The manual [`Published release pilot`](../.github/workflows/release-pilot.yml) workflow starts its timer before checkout, invokes the public `v0.4.0` Action against synthetic fixtures, verifies the expected policy result, generates a privacy-safe measurement, and preserves both artifacts for 14 days. This proves release resolution and integration mechanics; it does not count as an independent adopter project or production precision evidence.
