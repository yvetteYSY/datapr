import json
from pathlib import Path
import subprocess
import sys
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads(
    (ROOT / "contracts/public-v1.json").read_text(encoding="utf-8")
)


class PublicContractTest(unittest.TestCase):
    def _help(self, *arguments: str) -> str:
        result = subprocess.run(
            [sys.executable, "-m", "datapr.cli", *arguments, "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return result.stdout

    def test_cli_contract_is_present(self) -> None:
        root_help = self._help()
        for command in CONTRACT["cli"]["commands"]:
            self.assertIn(command, root_help)
        for option in CONTRACT["cli"]["global_options"]:
            self.assertIn(option, root_help)
        for command in CONTRACT["cli"]["commands"]:
            help_text = self._help(command)
            for argument in CONTRACT["cli"][command]:
                self.assertIn(argument, help_text)

    def test_action_contract_is_present(self) -> None:
        metadata = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))
        self.assertTrue(set(CONTRACT["action"]["inputs"]) <= set(metadata["inputs"]))
        self.assertTrue(
            set(CONTRACT["action"]["outputs"]) <= set(metadata["outputs"])
        )

    def test_schema_and_finding_contract_is_present(self) -> None:
        for path in CONTRACT["schemas"].values():
            self.assertTrue((ROOT / path).is_file(), path)
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((ROOT / "src/datapr").glob("*.py"))
        )
        for finding_id in CONTRACT["finding_ids"]:
            self.assertIn(f'"{finding_id}"', source)


if __name__ == "__main__":
    unittest.main()
