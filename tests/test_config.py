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
""",
                encoding="utf-8",
            )
            config = load_config(path)
        self.assertEqual(frozenset({"model.removed"}), config.policy.fail_on)
        self.assertEqual(3, config.policy.downstream_models)
        self.assertEqual(500, config.execution.sample_rows)
        self.assertEqual("first", config.execution.sample_strategy)
        self.assertEqual(17, config.execution.sample_seed)

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

    def test_rejects_unknown_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "datapr.yml"
            path.write_text("version: 2\n", encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
