"""The lineage declaration must live in active, unambiguous Markdown."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import validate_beyvra_fabric as validator


class BranchMapContractTests(unittest.TestCase):
    def validate(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.md"
            path.write_text(text)
            with patch.object(validator, "BRANCH_MAP_PATH", path):
                validator.validate_branch_map()

    def test_current_map(self):
        self.validate(validator.BRANCH_MAP_PATH.read_text())

    def test_commented_or_fenced_declarations_do_not_count(self):
        text = validator.BRANCH_MAP_PATH.read_text()
        for template in ("<!--\n{}\n-->", "```\n{}\n```", "~~~markdown\n{}\n~~~", "<!--\n{}"):
            with self.subTest(template=template), self.assertRaises(SystemExit):
                self.validate(template.format(text))

    def test_missing_modified_or_duplicate_declaration_is_rejected(self):
        text = validator.BRANCH_MAP_PATH.read_text()
        for line in validator.EXPECTED_BRANCH_REFS:
            variants = (text.replace(line, ""), text.replace(line, line + " wrong"),
                        text + "\n" + line, text + "\n" + line.split(":", 1)[0] + ": `other/branch`")
            for variant in variants:
                with self.subTest(line=line, variant=variant), self.assertRaises(SystemExit):
                    self.validate(variant)

    def test_unreadable_map_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(validator, "BRANCH_MAP_PATH", Path(directory) / "missing.md"):
                with self.assertRaises(SystemExit):
                    validator.validate_branch_map()
