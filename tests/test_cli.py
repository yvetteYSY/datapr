import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from datapr.cli import main
from datapr.render import MARKER


FIXTURES = Path(__file__).parent / "fixtures"


class CliTest(unittest.TestCase):
    def test_writes_markdown_and_enforces_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.md"
            exit_code = main(
                [
                    "compare",
                    "--base-manifest",
                    str(FIXTURES / "base_manifest.json"),
                    "--head-manifest",
                    str(FIXTURES / "head_manifest.json"),
                    "--format",
                    "markdown",
                    "--out",
                    str(report),
                    "--enforce",
                ]
            )
            contents = report.read_text(encoding="utf-8")

        self.assertEqual(1, exit_code)
        self.assertIn(MARKER, contents)
        self.assertIn("DataPR: FAIL", contents)

    def test_reports_usage_error_for_missing_inputs(self) -> None:
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            exit_code = main(["compare"])
        self.assertEqual(2, exit_code)
        self.assertIn("provide BASE..HEAD", error.getvalue())

    def test_writes_privacy_safe_adoption_measurement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "measurement.json"
            exit_code = main(
                [
                    "measure",
                    "--base-manifest",
                    str(FIXTURES / "base_manifest.json"),
                    "--head-manifest",
                    str(FIXTURES / "head_manifest.json"),
                    "--out",
                    str(output),
                ]
            )
            measurement = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(0, exit_code)
        self.assertEqual("1.0", measurement["measurement_schema_version"])
        self.assertGreaterEqual(measurement["analysis_seconds"], 0)
        self.assertEqual(1, measurement["models"]["changed"])
        self.assertNotIn("base_manifest", measurement)


if __name__ == "__main__":
    unittest.main()
