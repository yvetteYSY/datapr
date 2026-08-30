from pathlib import Path
import unittest

from datapr.analyzer import compare
from datapr.manifest import ManifestError, load_manifest


FIXTURES = Path(__file__).parent / "fixtures"


class AnalyzerTest(unittest.TestCase):
    def test_detects_schema_change_and_downstream_impact(self) -> None:
        result = compare(
            load_manifest(FIXTURES / "base_manifest.json"),
            load_manifest(FIXTURES / "head_manifest.json"),
        )

        self.assertEqual(1, len(result.changes))
        change = result.changes[0]
        self.assertEqual("orders", change.name)
        self.assertEqual(("daily_revenue",), change.downstream)
        self.assertEqual(
            [("customer_id", "type_changed"), ("order_status", "added")],
            [(column.column, column.kind) for column in change.columns],
        )

    def test_rejects_non_manifest_json(self) -> None:
        with self.assertRaises(ManifestError):
            load_manifest(FIXTURES / "not-a-manifest.json")


if __name__ == "__main__":
    unittest.main()
