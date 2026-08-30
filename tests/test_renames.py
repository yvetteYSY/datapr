import json
import unittest

from datapr.analyzer import compare
from datapr.config import PolicyConfig
from datapr.manifest import load_manifest_text
from datapr.policy import apply_policy
from datapr.renames import add_rename_candidates


def manifest(*nodes: dict, dialect: str = "postgres"):
    return load_manifest_text(
        json.dumps(
            {
                "metadata": {"adapter_type": dialect},
                "nodes": {node["unique_id"]: node["payload"] for node in nodes},
            }
        )
    )


def model(
    unique_id: str,
    name: str,
    sql: str,
    columns: dict[str, str],
    checksum: str,
) -> dict:
    return {
        "unique_id": unique_id,
        "payload": {
            "resource_type": "model",
            "name": name,
            "compiled_code": sql,
            "checksum": {"checksum": checksum},
            "columns": {
                column: {"name": column, "data_type": data_type}
                for column, data_type in columns.items()
            },
            "depends_on": {"nodes": []},
        },
    }


class RenameCandidateTest(unittest.TestCase):
    def test_detects_column_alias_rename_but_keeps_breaking_findings(self) -> None:
        base = manifest(
            model(
                "model.demo.orders",
                "orders",
                "select customer_id as buyer_id from raw_orders",
                {"buyer_id": "bigint"},
                "v1",
            )
        )
        head = manifest(
            model(
                "model.demo.orders",
                "orders",
                "select customer_id as customer_key from raw_orders",
                {"customer_key": "bigint"},
                "v2",
            )
        )

        result = add_rename_candidates(compare(base, head), base, head)
        rename = next(
            finding for finding in result.findings
            if finding.id == "rename.column_candidate"
        )

        self.assertEqual(0.95, rename.confidence)
        self.assertEqual("inferred", rename.provenance)
        self.assertFalse(rename.evidence["blocking"])
        self.assertIn("schema.removed_column", {item.id for item in result.findings})
        self.assertEqual("fail", apply_policy(result, PolicyConfig()).decision)
        self.assertEqual(1, result.coverage["rename_analysis"]["candidates"])

    def test_detects_unambiguous_model_rename(self) -> None:
        base = manifest(
            model(
                "model.demo.orders",
                "orders",
                "select order_id from raw_orders",
                {"order_id": "bigint"},
                "same-content",
            )
        )
        head = manifest(
            model(
                "model.demo.customer_orders",
                "customer_orders",
                "select order_id from raw_orders",
                {"order_id": "bigint"},
                "same-content",
            )
        )

        result = add_rename_candidates(compare(base, head), base, head)
        rename = next(
            finding for finding in result.findings
            if finding.id == "rename.model_candidate"
        )

        self.assertEqual("orders", rename.evidence["before_name"])
        self.assertEqual("customer_orders", rename.evidence["after_name"])
        self.assertEqual(0.98, rename.confidence)

    def test_skips_ambiguous_model_matches(self) -> None:
        base = manifest(
            model("model.demo.a", "a", "select 1 as id", {"id": "int"}, "same"),
            model("model.demo.b", "b", "select 1 as id", {"id": "int"}, "same"),
        )
        head = manifest(
            model("model.demo.c", "c", "select 1 as id", {"id": "int"}, "same"),
            model("model.demo.d", "d", "select 1 as id", {"id": "int"}, "same"),
        )

        result = add_rename_candidates(compare(base, head), base, head)

        self.assertNotIn("rename.model_candidate", {item.id for item in result.findings})
        self.assertGreater(
            result.coverage["rename_analysis"]["ambiguous_pairs_skipped"], 0
        )

    def test_does_not_guess_column_rename_from_type_alone(self) -> None:
        base = manifest(
            model(
                "model.demo.orders",
                "orders",
                "select customer_id as buyer_id from raw_orders",
                {"buyer_id": "bigint"},
                "v1",
            )
        )
        head = manifest(
            model(
                "model.demo.orders",
                "orders",
                "select order_id as customer_key from raw_orders",
                {"customer_key": "bigint"},
                "v2",
            )
        )

        result = add_rename_candidates(compare(base, head), base, head)

        self.assertNotIn("rename.column_candidate", {item.id for item in result.findings})


if __name__ == "__main__":
    unittest.main()
