"""Mutation checks for the source-only integration dependency boundary."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import validate_beyvra_fabric as validator


class N8nDependencyPinsTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(validator.N8N_MANIFEST_PATH.read_text())
        self.fabric = validator.load_json(validator.FABRIC_PATH)

    def validate(self, manifest):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest))
            with patch.object(validator, "N8N_MANIFEST_PATH", path):
                validator.validate_n8n_manifest(self.fabric)

    def test_dependencies_are_required_and_exactly_typed(self):
        variants = [None, {}, [], "unreviewed"]
        for field, value in self.manifest["dependencies"].items():
            bad = copy.deepcopy(self.manifest["dependencies"])
            bad[field] = True if type(value) is int else "unreviewed"
            variants.append(bad)
            missing = copy.deepcopy(self.manifest["dependencies"])
            del missing[field]
            variants.append(missing)
        extra = dict(self.manifest["dependencies"], unreviewed_authority=1)
        variants.append(extra)
        for dependencies in variants:
            with self.subTest(dependencies=dependencies), self.assertRaises(SystemExit):
                self.validate(dict(self.manifest, dependencies=dependencies))

    def test_repository_identity_is_canonical(self):
        for repository in (None, "appolon1908-hue/beyvra-backend", "other/backend"):
            with self.subTest(repository=repository), self.assertRaises(SystemExit):
                self.validate(dict(self.manifest, repository=repository))

    def test_readme_must_retain_dependency_pins(self):
        readme = validator.N8N_README_PATH.read_text()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "README.md"
            path.write_text(readme.replace("N8N PR #9 control-plane contract", "N8N PR #999"))
            with patch.object(validator, "N8N_README_PATH", path), self.assertRaises(SystemExit):
                self.validate(self.manifest)

    def test_current_dependency_contract(self):
        self.validate(self.manifest)
