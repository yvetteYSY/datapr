import json
from pathlib import Path
import tempfile
import unittest

from datapr.manifest import ManifestError, ManifestLimits, load_manifest, load_manifest_text


def payload(node: object | None = None) -> str:
    selected_node = (
        {
            "resource_type": "model",
            "name": "orders",
            "columns": {"id": {"data_type": "bigint"}},
            "depends_on": {"nodes": []},
            "compiled_code": "select 1 as id",
        }
        if node is None
        else node
    )
    return json.dumps(
        {
            "nodes": {
                "model.demo.orders": selected_node
            }
        }
    )


class ManifestLimitsTest(unittest.TestCase):
    def test_rejects_manifest_larger_than_byte_limit_before_parsing(self) -> None:
        with self.assertRaisesRegex(ManifestError, "limit is 10"):
            load_manifest_text(payload(), limits=ManifestLimits(max_bytes=10))

    def test_rejects_file_larger_than_limit_before_reading(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(payload(), encoding="utf-8")
            with self.assertRaisesRegex(ManifestError, "limit is 10"):
                load_manifest(path, limits=ManifestLimits(max_bytes=10))

    def test_rejects_excess_nodes_columns_and_sql(self) -> None:
        limits = ManifestLimits(max_nodes=0)
        with self.assertRaisesRegex(ManifestError, "contains 1 nodes"):
            load_manifest_text(payload(), limits=limits)

        limits = ManifestLimits(max_columns_per_model=0)
        with self.assertRaisesRegex(ManifestError, "contains 1 columns"):
            load_manifest_text(payload(), limits=limits)

        limits = ManifestLimits(max_sql_chars=3)
        with self.assertRaisesRegex(ManifestError, "SQL exceeds 3 characters"):
            load_manifest_text(payload(), limits=limits)

    def test_rejects_malformed_model_shapes_with_controlled_errors(self) -> None:
        cases = [
            ([], "node model.demo.orders must be an object"),
            ({"resource_type": "model", "columns": []}, "columns must be an object"),
            (
                {"resource_type": "model", "columns": {"id": "bigint"}},
                "column metadata must be objects",
            ),
            (
                {"resource_type": "model", "columns": {}, "depends_on": []},
                "depends_on must be an object",
            ),
            (
                {
                    "resource_type": "model",
                    "columns": {},
                    "depends_on": {"nodes": "model.demo.raw"},
                },
                "dependencies must be a list of strings",
            ),
            (
                {"resource_type": "model", "columns": {}, "compiled_code": {}},
                "field 'compiled_code' must be text",
            ),
        ]
        for node, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ManifestError, message):
                    load_manifest_text(payload(node))

    def test_rejects_deeply_nested_json_as_manifest_error(self) -> None:
        text = "[" * 2_000 + "]" * 2_000
        with self.assertRaises(ManifestError):
            load_manifest_text(text)


if __name__ == "__main__":
    unittest.main()
