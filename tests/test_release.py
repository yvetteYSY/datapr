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
        self.assertEqual("0.3.0", __version__)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        release_notes = (ROOT / "docs/releases/v0.3.0.md").read_text(
            encoding="utf-8"
        )
        project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('version = "0.3.0"', project)
        self.assertIn("## [0.3.0]", changelog)
        self.assertIn("# DataPR v0.3.0", release_notes)

    def test_consumer_examples_use_release_tag(self) -> None:
        for path in (ROOT / "README.md", ROOT / "docs/github-action.md"):
            contents = path.read_text(encoding="utf-8")
            self.assertIn("yvetteYSY/datapr@v0", contents)
            self.assertNotIn("yvetteYSY/datapr@main", contents)


if __name__ == "__main__":
    unittest.main()
