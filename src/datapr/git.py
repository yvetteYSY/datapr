"""Resolve dbt artifacts from Git revisions without changing the worktree."""

from __future__ import annotations

import subprocess
from pathlib import Path

from datapr.manifest import Manifest, ManifestError, load_manifest, load_manifest_text


class GitError(ValueError):
    """Raised when revision-aware artifact loading fails."""


def parse_range(value: str) -> tuple[str, str]:
    separator = "..." if "..." in value else ".."
    parts = value.split(separator)
    if len(parts) != 2 or not all(parts):
        raise GitError("revision range must look like BASE..HEAD")
    return parts[0], parts[1]


def _git_show(repo: Path, revision: str, artifact_path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{revision}:{artifact_path}"],
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
) -> tuple[Manifest, Manifest]:
    base_ref, head_ref = parse_range(revision_range)
    repo_path = Path(repo)
    base = load_manifest_text(
        _git_show(repo_path, base_ref, artifact_path),
        f"{base_ref}:{artifact_path}",
    )
    working_artifact = repo_path / artifact_path
    if head_ref == "HEAD" and working_artifact.exists():
        head = load_manifest(working_artifact)
    else:
        head = load_manifest_text(
            _git_show(repo_path, head_ref, artifact_path),
            f"{head_ref}:{artifact_path}",
        )
    return base, head
