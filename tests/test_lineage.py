import json
from pathlib import Path
import unittest

from datapr.analyzer import compare
from datapr.lineage import add_column_lineage, add_sql_risk_findings
from datapr.manifest import load_manifest_text, load_manifest


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

    def test_detects_removed_filter_and_added_cross_join(self) -> None:
        def artifact(sql: str, checksum: str):
            return load_manifest_text(
                """{"nodes":{"model.demo.orders":{"resource_type":"model","name":"orders","checksum":{"checksum":"%s"},"compiled_code":%s,"columns":{},"depends_on":{"nodes":[]}}}}"""
                % (checksum, __import__("json").dumps(sql))
            )

        base = artifact("select id from orders where created_at > current_date - 7", "v1")
        head = artifact("select * from orders cross join customers", "v2")
        result = add_sql_risk_findings(compare(base, head), base, head)
        ids = {finding.id for finding in result.findings}

        self.assertIn("performance.filter_removed", ids)
        self.assertIn("performance.cross_join_added", ids)
        self.assertIn("performance.select_star_added", ids)

    def test_dialect_capability_matrix(self) -> None:
        cases = json.loads((FIXTURES / "dialects" / "cases.json").read_text())
        for case in cases:
            with self.subTest(dialect=case["dialect"]):
                base = load_manifest_text(
                    json.dumps(
                        {
                            "metadata": {"adapter_type": case["dialect"]},
                            "nodes": {},
                        }
                    )
                )
                head = load_manifest_text(
                    json.dumps(
                        {
                            "metadata": {"adapter_type": case["dialect"]},
                            "nodes": {
                                "model.demo.orders": {
                                    "resource_type": "model",
                                    "name": "orders",
                                    "checksum": {"checksum": "v1"},
                                    "compiled_code": case["sql"],
                                    "columns": {},
                                    "depends_on": {"nodes": []},
                                }
                            },
                        }
                    )
                )
                result = add_column_lineage(compare(base, head), head)
                self.assertEqual(case["expected"], result.column_lineage["orders"])
                self.assertEqual([], result.coverage["sql_parse_failures"])


if __name__ == "__main__":
    unittest.main()
