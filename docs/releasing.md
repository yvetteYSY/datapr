# Release process

DataPR is both a Python project and a composite GitHub Action. GitHub releases are
the supported distribution mechanism. PyPI publication is optional and does not
block v1 engineering readiness.

## Release checklist

1. Create a release branch from protected `main`.
2. Update the package version, changelog, release notes, and consumer examples.
3. Run `python scripts/verify_release.py` locally.
4. Run the full unit, golden, package, action-smoke, synthetic-partner, and dogfood checks through a pull request.
5. Squash-merge without bypassing branch protection.
6. Create and push an immutable semantic release tag such as `v0.5.0` at the verified merge commit.
7. Let the tag-triggered release workflow rebuild, inspect, install, attest, and attach the wheel and source distribution to a GitHub release.
8. Move the compatible major tag, currently `v0`, to the same commit.
9. Run the published-release pilot and verify consumers can resolve both tags.

Release-candidate versions use PEP 440 tags such as `v1.0.0rc1`. The release
workflow marks tags containing `rc` as GitHub prereleases. Release candidates do
not advance the stable movable `v0` tag or create the future `v1` tag.

## Tag policy

- Semantic tags such as `v0.4.0` and `v0.5.0` identify exact releases and are never moved.
- `v0` moves only to backwards-compatible v0 releases.
- Starting with v1, `v1` moves only within the documented v1 compatibility policy.
- Consumers with stronger supply-chain requirements should pin a full commit SHA.

Because `main` is protected, release preparation must not be pushed directly. Tags
are created only after the exact main commit passes required CI. The release
workflow also rejects tags whose commit is not contained in `main` or whose name
does not match the package version.

## Package ownership

PyPI publication is not part of v0.5. Before enabling it, confirm project-name
ownership, configure a protected `pypi` GitHub environment and a PyPI trusted
publisher, publish a release candidate, and add the PyPI artifact to the
clean-install checks. GitHub release assets remain the supported path until that
setup is complete.
