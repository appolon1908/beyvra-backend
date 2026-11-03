"""Keep operational examples tied to the actual state and event authorities."""

import json
from pathlib import Path
import re
import runpy
import unittest

from jsonschema import Draft7Validator, FormatChecker
import yaml

ROOT = Path(__file__).resolve().parents[1]


class RecoveryRunbookContractTests(unittest.TestCase):
    def test_order_state_table_matches_canonical_transition_authority(self):
        authority = runpy.run_path(str(ROOT / "FX/apps/trading/domain/orders.py"))
        expected = {
            str(state): {
                str(target) for target in authority["TRANSITIONS"].get(state, set())
            }
            for state in authority["OrderState"]
        }
        actual = {}
        for line in (ROOT / "docs/ORDER-LIFECYCLE.md").read_text().splitlines():
            if not line.startswith("| "):
                continue
            state, targets = [cell.strip() for cell in line.strip("|").split("|")]
            if state == "Current state":
                continue
            self.assertNotIn(state, actual)
            actual[state] = (
                set() if targets == "(terminal)" else set(targets.split(", "))
            )
        self.assertEqual(actual, expected)

    def test_realtime_example_conforms_to_checked_in_target_envelope(self):
        text = (ROOT / "docs/REALTIME-RECOVERY.md").read_text()
        examples = re.findall(r"```json\n(.*?)\n```", text, re.S)
        self.assertEqual(len(examples), 1)
        document = yaml.safe_load(
            (ROOT / "contracts/asyncapi/beyvra-asyncapi-3.0.yaml").read_text()
        )
        validator = Draft7Validator(
            document["components"]["schemas"]["EventEnvelope"],
            format_checker=FormatChecker(),
        )
        validator.validate(json.loads(examples[0]))
