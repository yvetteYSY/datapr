import json
from pathlib import Path
import unittest

from datapr.analyzer import compare
from datapr.config import PolicyConfig
from datapr.lineage import add_column_lineage
from datapr.manifest import load_manifest
from datapr.policy import apply_policy
from datapr.render import render_json, render_markdown


TESTS = Path(__file__).parent
FIXTURES = Path("tests/fixtures")
GOLDEN = TESTS / "golden"


def _result():
    head = load_manifest(FIXTURES / "head_manifest.json")
    result = compare(load_manifest(FIXTURES / "base_manifest.json"), head)
    result = add_column_lineage(result, head)
    return apply_policy(result, PolicyConfig())


class RenderTest(unittest.TestCase):
    def test_markdown_matches_golden_report(self) -> None:
        expected = (GOLDEN / "manifest-change.md").read_text(encoding="utf-8")
        self.assertEqual(expected.rstrip("\n"), render_markdown(_result()))

    def test_json_matches_golden_contract(self) -> None:
        expected = json.loads(
            (GOLDEN / "manifest-change.json").read_text(encoding="utf-8")
        )
        self.assertEqual(expected, json.loads(render_json(_result())))


if __name__ == "__main__":
    unittest.main()
