# Beyvra backend — GitHub repository identity transfer

The protected production-orchestrator validator still recognized the former
owner `appolon1908-hue/beyvra-backend`. GitHub now reports canonical
`appolon1908/beyvra-backend` with **the same immutable GitHub repository ID
1319831182**. As a result, the job rejected every unrelated pull request as
`repository is outside the protected catalog identity map`.

This migration changes **only the exact canonical repository key** in the
repository's existing validator and release-intent tables and the contract's
`repository` field. It deliberately preserves:

- Repository ID `1319831182`, application role and deployment authority;
- `runtime_mutation_authority = false`, required check names and branch gates;
- Default-deny live trading, payments, calls, messages and external effects;
- Existing historical `ghcr.io/appolon1908-hue/...` image registry locations,
  attestation predicate and signing origins until their live provenance and
  availability are independently verified.

No alternate owner wildcard, spoofable alias, weakened signature check,
unreviewed registry cutover, or default-allow rule is added. The retired owner
is explicitly **rejected** as a current GitHub repository identity after this
change. Migration of other transferred projects must have its own independently
verified current repository IDs and protected review.

## Exact local certification

```bash
GITHUB_REPOSITORY=appolon1908/beyvra-backend \
GITHUB_REPOSITORY_ID=1319831182 \
python3 .codestra/validate-production-orchestrator-contract.py

python3 -m unittest discover -s .codestra/tests \
  -p test_repository_identity_transfer.py -v
```

A passing contract execution and four local regression tests prove the exact
renamed ID is recognized and the previous name / altered numeric ID are
rejected. This is **not** an external security attestation or protected-main
certification. The candidate changes governance-critical authority code and
therefore requires an independent security/CODEOWNER review and successful
exact-head hosted protected orchestrator contract, complete validation, and
promotion checks before a merge into `development` or any higher environment.

In particular: do not disable the `orchestrator-contract` workflow or
treat the repository transfer as authorization for financial effects.
Production GO=NO; PAPER-only.
