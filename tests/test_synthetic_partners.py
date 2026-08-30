import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "examples" / "synthetic_partners" / "run.py"


class SyntheticPartnerTests(unittest.TestCase):
    def test_all_functional_prototypes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(RUNNER), "--out-dir", directory],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            summary = json.loads(result.stdout)
            self.assertTrue(summary["synthetic"])
            self.assertEqual(
                {item["prototype"] for item in summary["prototypes"]},
                {"commerce_bigquery", "fintech_snowflake", "saas_postgres"},
            )
            self.assertTrue(
                all(item["coverage_complete"] for item in summary["prototypes"])
            )
            profile = next(
                item
                for item in summary["prototypes"]
                if item["prototype"] == "saas_postgres"
            )
            self.assertTrue(profile["differential_execution"])


if __name__ == "__main__":
    unittest.main()
