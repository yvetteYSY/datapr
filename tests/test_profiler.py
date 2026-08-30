import csv
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

        ids = {finding.id for finding in profiled.findings}
        self.assertIn("profile.row_count_changed", ids)
        self.assertIn("profile.null_rate_changed", ids)
        self.assertIn("profile.distribution_changed", ids)
        self.assertEqual(1, profiled.coverage["profiled_models"])
        self.assertTrue(profiled.coverage["complete"])

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
