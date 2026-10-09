# Beyvra backend — patched authentication/network dependencies

## Scope

This branch addresses the eight high/critical Python findings reported by
the container scan for backend PR #146. It consolidates the already existing
Dependabot proposals [#139 (PyJWT)](https://github.com/appolon1908/beyvra-backend/pull/139)
and [#142 (urllib3)](https://github.com/appolon1908/beyvra-backend/pull/142)
for the **development** lane. It does not replace or weaken the protected
orchestrator catalog or promotion rules.

Exactly two pinned runtime dependencies change in `FX/requirements.txt`:

- `PyJWT[crypto]==2.15.0` (previously 2.13.0; fixes reported token-signing,
  JWKS, and algorithm-confusion vulnerabilities).
- `urllib3==2.8.0` (previously 2.7.0; fixes reported HTTPS proxy and chunk
  parser vulnerabilities).

The existing Keycloak BFF uses `jwt.decode(..., algorithms=["RS256"])`,
issuer, audience, and required claims. Those verification requirements are
unchanged. No broker, order, deposit, withdrawal, live payment, secret, or
financial execution behavior is enabled or modified.

## Verification

Run in an isolated Python environment, without a live tenant or brokers:

```bash
python -m pip install -r FX/requirements.txt
python -m unittest FX.security.tests.test_runtime_dependency_security -v
python -m pip check
```

The targeted regression tests reject HS256 tokens on the RS256 path and
tokens missing required claims or carrying an incorrect issuer/audience.
They also verify the new exact dependency pins.

**Source-level verification alone is insufficient.** The actual rebuilt
runtime image MUST pass Trivy with no high/critical findings and the complete
repository CI/tests on the exact branch head. Keycloak/JWKS/tenant replay
negative tests and the centrally maintained protected catalog identity /
promotion path must independently pass before merge or staging. Do not mark
expected PostgreSQL constraint-denial test logs as a real test failure without
checking the pytest summary. Do not make the CI green by excluding PyJWT,
urllib3, changing severity thresholds, disabling image scanning or weakening
required governance checks.

## Rollout and rollback

The candidate targets `development`, never protected `main` or production
directly. Obtain independent review and a successful exact-SHA CI,
merge through the approved branch policy, rebuild and rescan, and only then
retire the redundant Dependabot branches through a separate governance
decision. Keep PAPER-only operation; `PRODUCTION_GO=NO` and all financial
external effects disabled until separately certified.
