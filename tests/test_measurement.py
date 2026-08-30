import json
from pathlib import Path
import unittest

from datapr.analyzer import compare
from datapr.lineage import add_column_lineage, add_sql_risk_findings
from datapr.manifest import load_manifest
from datapr.measurement import build_measurement, render_measurement
from datapr.policy import apply_policy
from datapr.config import PolicyConfig
from datapr.renames import add_rename_candidates


FIXTURES = Path(__file__).parent / "fixtures"


class MeasurementTest(unittest.TestCase):
    def test_builds_aggregate_privacy_safe_measurement(self) -> None:
        base = load_manifest(FIXTURES / "base_manifest.json")
        head = load_manifest(FIXTURES / "head_manifest.json")
        result = compare(base, head)
        result = add_sql_risk_findings(result, base, head)
        result = add_rename_candidates(result, base, head)
        result = add_column_lineage(result, head)
        result = apply_policy(result, PolicyConfig())

        measurement = build_measurement(result, 0.1234567)
        serialized = render_measurement(result, 0.1234567)

        self.assertEqual("1.0", measurement["measurement_schema_version"])
        self.assertEqual(0.123457, measurement["analysis_seconds"])
        self.assertEqual(1, measurement["models"]["changed"])
        self.assertEqual(len(result.findings), measurement["findings"]["total"])
        self.assertEqual(
            len(result.coverage["sql_parse_failures"]),
            measurement["coverage"]["sql_parse_failure_count"],
        )
        self.assertEqual(measurement, json.loads(serialized))
        for sensitive in (
            str(FIXTURES),
            "orders",
            "daily_revenue",
            "customer_id",
            "select o.order_id",
        ):
            self.assertNotIn(sensitive.casefold(), serialized.casefold())

    def test_clamps_negative_elapsed_time(self) -> None:
        base = load_manifest(FIXTURES / "base_manifest.json")
        result = compare(base, base)
        self.assertEqual(0.0, build_measurement(result, -1.0)["analysis_seconds"])


if __name__ == "__main__":
    unittest.main()
