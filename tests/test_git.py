import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from datapr.git import GitError, manifests_from_range, parse_range


def _run(repo: Path, *args: str) -> None:
    subprocess.run(args, cwd=repo, check=True, capture_output=True)


def _manifest(checksum: str) -> str:
    return json.dumps(
        {
            "nodes": {
                "model.demo.orders": {
                    "resource_type": "model",
                    "name": "orders",
                    "checksum": {"checksum": checksum},
                    "columns": {},
                    "depends_on": {"nodes": []},
                }
            }
        }
    )


class GitTest(unittest.TestCase):
    def test_parses_two_and_three_dot_ranges(self) -> None:
        self.assertEqual(("main", "HEAD"), parse_range("main..HEAD"))
        self.assertEqual(("main", "feature"), parse_range("main...feature"))
        with self.assertRaises(GitError):
            parse_range("main")

    def test_loads_base_commit_and_working_tree_head(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            artifact = repo / "artifacts" / "manifest.json"
            artifact.parent.mkdir()
            _run(repo, "git", "init", "-b", "main")
            _run(repo, "git", "config", "user.name", "DataPR Test")
            _run(repo, "git", "config", "user.email", "test@datapr.dev")
            artifact.write_text(_manifest("v1"), encoding="utf-8")
            _run(repo, "git", "add", ".")
            _run(repo, "git", "commit", "-m", "base")
            artifact.write_text(_manifest("v2"), encoding="utf-8")

            base, head = manifests_from_range(
                "main..HEAD", "artifacts/manifest.json", repo
            )

        self.assertEqual("v1", base.models["model.demo.orders"].fingerprint)
        self.assertEqual("v2", head.models["model.demo.orders"].fingerprint)


if __name__ == "__main__":
    unittest.main()
