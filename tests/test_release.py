import json
from pathlib import Path
import unittest

import yaml

from datapr import __version__


ROOT = Path(__file__).parent.parent


class ReleaseTest(unittest.TestCase):
    def test_action_metadata_is_marketplace_ready(self) -> None:
        metadata = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))
        self.assertEqual("DataPR - dbt Change Impact Review", metadata["name"])
        self.assertEqual("composite", metadata["runs"]["using"])
        self.assertEqual("git-pull-request", metadata["branding"]["icon"])
        self.assertIn("github-token", metadata["inputs"])

    def test_release_version_is_consistent(self) -> None:
        self.assertEqual("1.0.0rc1", __version__)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        release_notes = (ROOT / "docs/releases/v1.0.0rc1.md").read_text(
            encoding="utf-8"
        )
        project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('version = "1.0.0rc1"', project)
        self.assertIn("## [1.0.0rc1]", changelog)
        self.assertIn("# DataPR v1.0.0rc1", release_notes)

    def test_release_verifier_accepts_current_tree(self) -> None:
        from scripts.verify_release import verify_release

        self.assertEqual([], verify_release("v1.0.0rc1"))

    def test_consumer_examples_use_release_tag(self) -> None:
        for path in (ROOT / "README.md", ROOT / "docs/github-action.md"):
            contents = path.read_text(encoding="utf-8")
            self.assertIn("yvetteYSY/datapr@v0", contents)
            self.assertNotIn("yvetteYSY/datapr@main", contents)

    def test_pilot_uses_immutable_release_with_bounded_permissions(self) -> None:
        workflow = (ROOT / ".github/workflows/release-pilot.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("uses: yvetteYSY/datapr@v0.5.0", workflow)
        self.assertNotIn("uses: yvetteYSY/datapr@v0\n", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn('enforce: "false"', workflow)
        self.assertIn("timeout-minutes: 10", workflow)
        self.assertIn("retention-days: 14", workflow)

    def test_release_workflow_builds_attests_and_publishes(self) -> None:
        workflow = (ROOT / ".github/workflows/release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("python -m build", workflow)
        self.assertIn("python -m twine check", workflow)
        self.assertIn("actions/attest-build-provenance@v3", workflow)
        self.assertIn('gh release create "$GITHUB_REF_NAME"', workflow)
        self.assertIn("--prerelease", workflow)
        self.assertIn("scripts/rehearse_upgrade.py", workflow)

    def test_candidate_pilot_uses_exact_tag_and_bounded_permissions(self) -> None:
        workflow = (
            ROOT / ".github/workflows/release-candidate-pilot.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("uses: yvetteYSY/datapr@v1.0.0rc1", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("timeout-minutes: 10", workflow)
        self.assertIn("retention-days: 14", workflow)
        self.assertIn('"datapr_version": "1.0.0rc1"', workflow)
        self.assertIn("datapr-1.0.0rc1-py3-none-any.whl", workflow)

    def test_pilot_measurement_is_privacy_safe_release_evidence(self) -> None:
        path = ROOT / "benchmarks/v0.4.0-pilot-measurement.json"
        measurement = json.loads(path.read_text(encoding="utf-8"))
        serialized = json.dumps(measurement).casefold()
        self.assertEqual("0.4.0", measurement["datapr_version"])
        self.assertEqual("fail", measurement["decision"])
        self.assertTrue(measurement["coverage"]["complete"])
        for sensitive in ("orders", "customer_id", "base_manifest", "head_manifest"):
            self.assertNotIn(sensitive, serialized)


if __name__ == "__main__":
    unittest.main()
