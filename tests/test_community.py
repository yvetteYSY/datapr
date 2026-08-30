from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).parent.parent
ISSUE_TEMPLATES = ROOT / ".github" / "ISSUE_TEMPLATE"


class CommunityMetadataTest(unittest.TestCase):
    def test_issue_forms_have_unique_fields_and_valid_labels(self) -> None:
        expected_labels = {
            "adopter-validation.yml": "adopter-feedback",
            "bug.yml": "bug",
            "feature.yml": "enhancement",
        }
        for filename, label in expected_labels.items():
            with self.subTest(filename=filename):
                form = yaml.safe_load(
                    (ISSUE_TEMPLATES / filename).read_text(encoding="utf-8")
                )
                ids = [item.get("id") for item in form["body"] if item.get("id")]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertIn(label, form["labels"])

    def test_pull_request_template_covers_contract_and_privacy(self) -> None:
        template = (ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Result-contract impact", template)
        self.assertIn("proprietary identifiers", template)


if __name__ == "__main__":
    unittest.main()
