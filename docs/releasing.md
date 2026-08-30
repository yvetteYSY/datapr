# Release process

DataPR is both a Python project and a composite GitHub Action. GitHub releases are the current distribution mechanism; PyPI publication is intentionally deferred.

## Release checklist

1. Create a release branch from protected `main`.
2. Update the package version, changelog, release notes, and consumer examples.
3. Run the full unit, golden, action-smoke, and dogfood checks through a pull request.
4. Squash-merge without bypassing branch protection.
5. Create an immutable semantic release tag such as `v0.2.0` at the merge commit.
6. Publish the GitHub release and Marketplace listing.
7. Move the compatible major tag, currently `v0`, to the same commit.
8. Verify a consumer workflow can resolve both tags.

## Tag policy

- Semantic tags such as `v0.1.0` and `v0.2.0` identify exact releases and are never moved.
- `v0` moves only to backwards-compatible v0 releases.
- Consumers with stronger supply-chain requirements should pin a full commit SHA.

Because `main` is protected, release preparation must not be pushed directly. Tags are created only after the exact main commit passes required CI.
