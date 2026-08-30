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
""",
                encoding="utf-8",
            )
            config = load_config(path)
        self.assertEqual(frozenset({"model.removed"}), config.policy.fail_on)
        self.assertEqual(3, config.policy.downstream_models)
        self.assertEqual(500, config.execution.sample_rows)

    def test_rejects_unknown_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "datapr.yml"
            path.write_text("version: 2\n", encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
