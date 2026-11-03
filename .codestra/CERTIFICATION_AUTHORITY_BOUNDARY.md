# Source verification and independent certification

The exact-SHA workflow proves which source commit was checked out, checks repository
integrity, and runs the committed source contract regressions. The evidence declares
`SOURCE_ONLY`, `runtime_certified=false`, and `production_activation_authorized=false`.
These checks are useful source evidence; they do not prove runtime, PostgreSQL,
provider, deployment, rollback, or independent controller acceptance.

The hierarchy workflow validates the manifest's source policy. It cannot issue
`codestra-control-plane` or `codestra/control-plane` certification from that policy.
The retained certification jobs fail with `EXTERNAL_CERTIFICATION_REQUIRED` until a
real independent certification integration exists. The exact-SHA workflow likewise
does not publish a successful target certification status from checkout and Git
integrity alone. Its token no longer requests status-write permission.

Required repository checks and protections are not changed by this PR. Do not
remove those checks, rename source validation to impersonate them, or fabricate a
receipt to make these gates green. The independent issuer must validate authentic
exact-revision runtime evidence and publish the status through its authorized
process. Wiring that issuer requires its actual interface and trusted identity.

Regression entry point: `python -m unittest scripts.test_certification_authority_boundary`.
The tests execute the committed certification-step shell scripts against a successful
source-policy result with no API credential and prove they neither return success
nor invoke the GitHub status publisher.
