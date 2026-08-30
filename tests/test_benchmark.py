import unittest

from benchmarks.manifest_scale import _manifest_pair, _run_once


class BenchmarkHarnessTest(unittest.TestCase):
    def test_generates_and_analyzes_requested_scale(self) -> None:
        base, head = _manifest_pair(100)

        self.assertEqual(100, len(base.models))
        self.assertEqual(100, len(head.models))
        self.assertEqual(1, _run_once(base, head))

    def test_rejects_non_positive_size(self) -> None:
        with self.assertRaises(ValueError):
            _manifest_pair(0)


if __name__ == "__main__":
    unittest.main()
