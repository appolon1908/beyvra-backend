"""Source-only workflows cannot mint independent runtime certification."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class CertificationAuthorityBoundaryTests(unittest.TestCase):
    def run_certification_step(self, workflow, job_id):
        data = yaml.safe_load((ROOT / '.github/workflows' / workflow).read_text())
        job = data['jobs'][job_id]
        step = job['steps'][-1]
        with tempfile.TemporaryDirectory() as directory:
            # Any accidental gh invocation is observable without granting API access.
            gh = Path(directory) / 'gh'
            gh.write_text('#!/bin/sh\nprintf unexpected-status-publication\\n\nexit 0\n')
            gh.chmod(0o700)
            result = subprocess.run(
                ['bash', '-c', step['run'].replace('${{ needs.hierarchy-governance.result }}', 'success')], text=True, capture_output=True,
                env={**os.environ, 'PATH': directory + os.pathsep + os.environ['PATH'],
                     'GITHUB_REPOSITORY': 'appolon1908/beyvra-backend',
                     'EXPECTED_SHA': '1' * 40, 'GITHUB_RUN_ID': 'unit-only',
                     'GITHUB_SERVER_URL': 'https://github.invalid'},
            )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('EXTERNAL_CERTIFICATION_REQUIRED', result.stdout + result.stderr)
        self.assertNotIn('unexpected-status-publication', result.stdout + result.stderr)
        self.assertNotIn('statuses', data.get('permissions', {}))

    def test_exact_source_checkout_cannot_publish_runtime_certification(self):
        self.run_certification_step('required-exact-sha-ci.yml', 'exact-sha')

    def test_manifest_validation_cannot_publish_controller_certification(self):
        for job_id in ('codestra-control-plane', 'codestra-slash-control-plane'):
            with self.subTest(job_id=job_id):
                self.run_certification_step('codestra-hierarchy-governance.yml', job_id)
