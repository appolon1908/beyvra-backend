"""The reviewed AsyncAPI validator is approved only at its exact source and argv."""

import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
POLICY = runpy.run_path(
    str(ROOT / ".codestra/validate-production-orchestrator-contract.py")
)


class AsyncApiSourceBindingTests(unittest.TestCase):
    def test_readonly_validator_is_recognized(self):
        with patch.dict(
            os.environ, {"GITHUB_REPOSITORY": "appolon1908/beyvra-backend"}
        ):
            self.assertTrue(
                POLICY["approved_read_only_script_invocation"](
                    "scripts/validate_asyncapi.mjs", [], ROOT
                )
            )

    def test_unreviewed_arguments_are_rejected(self):
        with patch.dict(
            os.environ, {"GITHUB_REPOSITORY": "appolon1908/beyvra-backend"}
        ):
            self.assertFalse(
                POLICY["approved_read_only_script_invocation"](
                    "scripts/validate_asyncapi.mjs", ["--execute"], ROOT
                )
            )

    def test_source_changes_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            base = Path(directory)
            (base / "scripts").mkdir()
            (base / "scripts/validate_asyncapi.mjs").write_text(
                (ROOT / "scripts/validate_asyncapi.mjs").read_text()
                + '\nfetch("https://example.invalid");\n'
            )
            with patch.dict(
                os.environ, {"GITHUB_REPOSITORY": "appolon1908/beyvra-backend"}
            ):
                self.assertFalse(
                    POLICY["approved_read_only_script_invocation"](
                        "scripts/validate_asyncapi.mjs", [], base
                    )
                )


if __name__ == "__main__":
    unittest.main()
