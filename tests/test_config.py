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


if __name__ == "__main__":
    unittest.main()
