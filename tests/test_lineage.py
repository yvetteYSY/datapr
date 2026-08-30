from pathlib import Path
import unittest

from datapr.analyzer import compare
from datapr.lineage import add_column_lineage
from datapr.manifest import load_manifest


FIXTURES = Path(__file__).parent / "fixtures"


class LineageTest(unittest.TestCase):
    def test_maps_output_columns_to_source_columns(self) -> None:
        head = load_manifest(FIXTURES / "head_manifest.json")
        result = add_column_lineage(
            compare(load_manifest(FIXTURES / "base_manifest.json"), head), head
        )

        self.assertEqual(
            ["o.customer_id"], result.column_lineage["orders"]["customer_id"]
        )
        self.assertEqual(["o.order_id"], result.column_lineage["orders"]["order_id"])
        self.assertEqual(1, result.coverage["column_lineage_models"])


if __name__ == "__main__":
    unittest.main()
