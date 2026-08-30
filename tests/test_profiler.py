import csv
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from datapr.analyzer import compare
from datapr.config import ExecutionConfig, PolicyConfig
from datapr.manifest import load_manifest
from datapr.profiler import ProfileError, add_profile_findings


FIXTURES = Path(__file__).parent / "fixtures"


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class ProfilerTest(unittest.TestCase):
    def test_profiles_row_count_nulls_and_numeric_distribution(self) -> None:
        result = compare(
            load_manifest(FIXTURES / "base_manifest.json"),
            load_manifest(FIXTURES / "head_manifest.json"),
        )
        with tempfile.TemporaryDirectory() as directory:
            base_dir, head_dir = Path(directory) / "base", Path(directory) / "head"
            base_dir.mkdir()
            head_dir.mkdir()
            _write_csv(
                base_dir / "orders.csv",
                [
                    {"order_id": 1, "amount": 10, "note": "ok"},
                    {"order_id": 2, "amount": 20, "note": "ok"},
                ],
            )
            _write_csv(
                head_dir / "orders.csv",
                [
                    {"order_id": 1, "amount": 100, "note": ""},
                    {"order_id": 2, "amount": 200, "note": "ok"},
                    {"order_id": 3, "amount": 300, "note": ""},
                ],
            )
            profiled = add_profile_findings(
                result,
                ExecutionConfig(
                    sample_rows=100,
                    base_data_dir=str(base_dir),
                    head_data_dir=str(head_dir),
                ),
                PolicyConfig(),
            )
            preserved_incomplete = add_profile_findings(
                replace(result, coverage={**result.coverage, "complete": False}),
                ExecutionConfig(
                    sample_rows=100,
                    base_data_dir=str(base_dir),
                    head_data_dir=str(head_dir),
                ),
                PolicyConfig(),
            )

        ids = {finding.id for finding in profiled.findings}
        self.assertIn("profile.row_count_changed", ids)
        self.assertIn("profile.null_rate_changed", ids)
        self.assertIn("profile.distribution_changed", ids)
        self.assertEqual(1, profiled.coverage["profiled_models"])
        self.assertTrue(profiled.coverage["complete"])
        self.assertEqual("hash", profiled.coverage["sample_strategy"])
        self.assertEqual("md5-json-v1", profiled.coverage["sample_hash"])
        self.assertFalse(preserved_incomplete.coverage["complete"])

    def test_hash_sample_is_independent_of_input_order(self) -> None:
        result = compare(
            load_manifest(FIXTURES / "base_manifest.json"),
            load_manifest(FIXTURES / "head_manifest.json"),
        )
        rows = [
            {"order_id": value, "amount": value * 10, "note": "ok"}
            for value in range(1, 101)
        ]
        changed = [
            {"order_id": value, "amount": value * 100, "note": "ok"}
            for value in range(1, 101)
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base_a, base_b, head = root / "base-a", root / "base-b", root / "head"
            base_a.mkdir()
            base_b.mkdir()
            head.mkdir()
            _write_csv(base_a / "orders.csv", rows)
            _write_csv(base_b / "orders.csv", list(reversed(rows)))
            _write_csv(head / "orders.csv", changed)

            def profile(base: Path):
                return add_profile_findings(
                    result,
                    ExecutionConfig(
                        sample_rows=10,
                        sample_strategy="hash",
                        sample_seed=42,
                        base_data_dir=str(base),
                        head_data_dir=str(head),
                    ),
                    PolicyConfig(),
                )

            forward = profile(base_a)
            reversed_input = profile(base_b)

        forward_distribution = next(
            finding for finding in forward.findings
            if finding.id == "profile.distribution_changed"
            and finding.evidence["column"] == "amount"
        )
        reversed_distribution = next(
            finding for finding in reversed_input.findings
            if finding.id == "profile.distribution_changed"
            and finding.evidence["column"] == "amount"
        )
        self.assertEqual(forward_distribution.evidence, reversed_distribution.evidence)
        self.assertEqual(42, forward_distribution.evidence["sample_seed"])

    def test_requires_both_data_directories(self) -> None:
        result = compare(
            load_manifest(FIXTURES / "base_manifest.json"),
            load_manifest(FIXTURES / "head_manifest.json"),
        )
        with self.assertRaises(ProfileError):
            add_profile_findings(
                result,
                ExecutionConfig(base_data_dir="missing"),
                PolicyConfig(),
            )


if __name__ == "__main__":
    unittest.main()
