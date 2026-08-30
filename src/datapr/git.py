"""Resolve dbt artifacts from Git revisions without changing the worktree."""

from __future__ import annotations

import subprocess
from pathlib import Path

from datapr.manifest import (
    DEFAULT_MANIFEST_LIMITS,
    Manifest,
    ManifestLimits,
    load_manifest,
    load_manifest_text,
)


class GitError(ValueError):
    """Raised when revision-aware artifact loading fails."""


def parse_range(value: str) -> tuple[str, str]:
    separator = "..." if "..." in value else ".."
    parts = value.split(separator)
    if len(parts) != 2 or not all(parts):
        raise GitError("revision range must look like BASE..HEAD")
    return parts[0], parts[1]


def _git_show(
    repo: Path,
    revision: str,
    artifact_path: str,
    limits: ManifestLimits = DEFAULT_MANIFEST_LIMITS,
) -> str:
    object_spec = f"{revision}:{artifact_path}"
    size_result = subprocess.run(
        ["git", "cat-file", "-s", object_spec],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    if size_result.returncode:
        detail = (
            size_result.stderr.strip().splitlines()[-1]
            if size_result.stderr.strip()
            else "not found"
        )
        raise GitError(f"cannot load {artifact_path} at {revision}: {detail}")
    try:
        size = int(size_result.stdout.strip())
    except ValueError as exc:
        raise GitError(
            f"cannot determine size of {artifact_path} at {revision}"
        ) from exc
    if size > limits.max_bytes:
        raise GitError(
            f"{object_spec} is {size:,} bytes; limit is {limits.max_bytes:,}"
        )
    result = subprocess.run(
        ["git", "show", object_spec],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "not found"
        raise GitError(f"cannot load {artifact_path} at {revision}: {detail}")
    return result.stdout


def manifests_from_range(
    revision_range: str,
    artifact_path: str,
    repo: str | Path = ".",
    *,
    limits: ManifestLimits = DEFAULT_MANIFEST_LIMITS,
) -> tuple[Manifest, Manifest]:
    base_ref, head_ref = parse_range(revision_range)
    repo_path = Path(repo)
    base = load_manifest_text(
        _git_show(repo_path, base_ref, artifact_path, limits),
        f"{base_ref}:{artifact_path}",
        limits=limits,
    )
    working_artifact = repo_path / artifact_path
    if head_ref == "HEAD" and working_artifact.exists():
        head = load_manifest(working_artifact, limits=limits)
    else:
        head = load_manifest_text(
            _git_show(repo_path, head_ref, artifact_path, limits),
            f"{head_ref}:{artifact_path}",
            limits=limits,
        )
    return base, head
