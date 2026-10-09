"""Beyvra's GitHub transfer must not alter immutable repository authority."""
from __future__ import annotations

import json
import os
import runpy
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / ".codestra/production-orchestrator-contract.v1.json"
VALIDATOR = ROOT / ".codestra/validate-production-orchestrator-contract.py"
EXPECTED_REPOSITORY = "appolon1908/beyvra-backend"
STABLE_ID = 1319831182


class RepositoryTransferSecurityTests(unittest.TestCase):
    def test_current_owner_keeps_exact_stable_identity_and_default_deny(self):
        c = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(c["repository"], EXPECTED_REPOSITORY)
        self.assertEqual(c["repository_id"], STABLE_ID)
        self.assertEqual(c["role"], "application")
        self.assertEqual(c["default_branch"], "main")
        self.assertFalse(c["runtime_mutation_authority"])
        for value in c["safety"].values():
            self.assertIs(value, False)

    def test_catalog_has_exact_owner_with_no_legacy_key_or_implicit_authority(self):
        namespace = runpy.run_path(str(VALIDATOR), run_name="identity_migration_tests")
        catalog = namespace["EXPECTED_IDENTITIES"]
        self.assertEqual(catalog[EXPECTED_REPOSITORY], (STABLE_ID, "application", True, False))
        self.assertNotIn("appolon1908-hue/beyvra-backend", catalog)
        images = namespace["EXPECTED_ARTIFACT_POLICIES"][EXPECTED_REPOSITORY][0]
        self.assertEqual(images, (
            "ghcr.io/appolon1908-hue/beyvra-backend",
            "ghcr.io/appolon1908-hue/beyvra-backend-edge",
        ))

    def _run_validator(self, repo: str, repository_id: int) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "GITHUB_REPOSITORY": repo,
               "GITHUB_REPOSITORY_ID": str(repository_id)}
        return subprocess.run(
            [sys.executable, str(VALIDATOR)],
            env=env, cwd=ROOT, text=True, capture_output=True, timeout=15,
            check=False,
        )

    def test_exact_transferred_identity_is_accepted(self):
        good = self._run_validator(EXPECTED_REPOSITORY, STABLE_ID)
        self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
        self.assertIn("PRODUCTION_ORCHESTRATOR_CONTRACT=PASS", good.stdout)

    def test_old_owner_and_wrong_repo_id_are_both_rejected(self):
        namespace = runpy.run_path(str(VALIDATOR), run_name="identity_rejection_tests")
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        with mock.patch.dict(os.environ, {
            "GITHUB_REPOSITORY": "appolon1908-hue/beyvra-backend",
            "GITHUB_REPOSITORY_ID": str(STABLE_ID),
        }):
            with self.assertRaisesRegex(
                namespace["ContractError"], "outside the protected catalog identity map"
            ):
                namespace["validate"](contract)

        with mock.patch.dict(os.environ, {
            "GITHUB_REPOSITORY": EXPECTED_REPOSITORY,
            "GITHUB_REPOSITORY_ID": str(STABLE_ID + 1),
        }):
            with self.assertRaisesRegex(namespace["ContractError"], "stable repository ID mismatch"):
                namespace["validate"](contract)


if __name__ == "__main__":
    unittest.main()
