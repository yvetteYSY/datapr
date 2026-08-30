from pathlib import Path
import tempfile
import unittest

from datapr.config import ConfigError, load_config


class ConfigTest(unittest.TestCase):
    def test_loads_policy_thresholds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "datapr.yml"
            path.write_text(
                """version: 1
policies:
  fail_on: [model.removed]
  downstream_models: 3
execution:
  sample_rows: 500
  sample_strategy: first
  sample_seed: 17
  max_sample_rows: 1000
  max_profile_models: 25
  max_profile_file_bytes: 2048
  max_profile_columns: 50
  memory_limit_mb: 128
""",
                encoding="utf-8",
            )
            config = load_config(path)
        self.assertEqual(frozenset({"model.removed"}), config.policy.fail_on)
        self.assertEqual(3, config.policy.downstream_models)
        self.assertEqual(500, config.execution.sample_rows)
        self.assertEqual("first", config.execution.sample_strategy)
        self.assertEqual(17, config.execution.sample_seed)
        self.assertEqual(1000, config.execution.max_sample_rows)
        self.assertEqual(25, config.execution.max_profile_models)
        self.assertEqual(2048, config.execution.max_profile_file_bytes)
        self.assertEqual(50, config.execution.max_profile_columns)
        self.assertEqual(128, config.execution.memory_limit_mb)

    def test_defaults_to_deterministic_hash_sampling(self) -> None:
        config = load_config(None)

        self.assertEqual("hash", config.execution.sample_strategy)
        self.assertEqual(0, config.execution.sample_seed)

    def test_rejects_unknown_sample_strategy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "datapr.yml"
            path.write_text(
                "version: 1\nexecution:\n  sample_strategy: random\n",
                encoding="utf-8",
            )
            with self.assertRaises(ConfigError):
                load_config(path)

    def test_rejects_sample_rows_above_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "datapr.yml"
            path.write_text(
                """version: 1
execution:
  sample_rows: 101
  max_sample_rows: 100
""",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ConfigError, "cannot exceed"):
                load_config(path)

    def test_rejects_non_positive_resource_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "datapr.yml"
            path.write_text(
                "version: 1\nexecution:\n  memory_limit_mb: 0\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ConfigError, "must be positive"):
                load_config(path)

    def test_rejects_unknown_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "datapr.yml"
            path.write_text("version: 2\n", encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_config(path)
            path.write_text("version: true\n", encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_config(path)

    def test_rejects_false_or_non_text_root_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "datapr.yml"
            path.write_text("false\n", encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "root must be a mapping"):
                load_config(path)
            path.write_text("version: 1\n1: value\n", encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "unknown 'root'"):
                load_config(path)

    def test_rejects_unknown_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "datapr.yml"
            path.write_text(
                "version: 1\npolicies:\n  fail_onn: []\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ConfigError, "fail_onn"):
                load_config(path)

    def test_rejects_negative_policy_thresholds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "datapr.yml"
            path.write_text(
                "version: 1\npolicies:\n  row_count_change_percent: -1\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ConfigError, "non-negative"):
                load_config(path)

    def test_rejects_mistyped_boolean_and_profile_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "datapr.yml"
            path.write_text(
                "version: 1\npolicies:\n  fail_on_incomplete_coverage: 'false'\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ConfigError, "must be a boolean"):
                load_config(path)
            path.write_text(
                "version: 1\nexecution:\n  base_data_dir: false\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ConfigError, "non-empty string"):
                load_config(path)

    def test_rejects_schema_invalid_numeric_and_duplicate_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "datapr.yml"
            invalid_payloads = (
                "version: 1\nexecution:\n  sample_rows: 1.5\n",
                "version: 1\nexecution:\n  sample_seed: 1.5\n",
                "version: 1\npolicies:\n  downstream_models: true\n",
                "version: 1\npolicies:\n  row_count_change_percent: .nan\n",
                "version: 1\npolicies:\n  fail_on: [model.removed, model.removed]\n",
            )
            for payload in invalid_payloads:
                with self.subTest(payload=payload):
                    path.write_text(payload, encoding="utf-8")
                    with self.assertRaises(ConfigError):
                        load_config(path)


if __name__ == "__main__":
    unittest.main()
