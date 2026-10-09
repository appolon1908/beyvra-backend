# Beyvra Postman API authority

Beyvra's committed OpenAPI documents are the API source of truth. Postman collections in this directory are derived certification artifacts.

Rules:
1. Preserve each OpenAPI contract boundary; do not collapse independent contracts into a competing master schema.
2. No credentials, account secrets, broker keys, trading tokens, private keys, or production secrets may be committed.
3. Newman runs default to local/staging-safe targets. Live order placement, money movement, settlement, or production trading effects require separate protected authorization.
4. Exact-head CI and independent review are required before merge.
5. Staging readback, rollback/recovery, and runtime evidence are required before production promotion.

Known contract overlap:
- `contracts/openapi/beyvra-workspace-v1.yaml` repeats 8 watchlist method/path pairs already present in `contracts/openapi/beyvra-openapi-3.1.yaml`.
- Do not delete or merge these source contracts from a Postman-only mission. Resolve ownership in the API contract layer first, then regenerate collections.

Current generated coverage:
- Enterprise Experience: 26 operations
- Core Trading API: 700 operations
- Treasury: 37 operations
- Workspace: 8 operations
- Codestra Real Wallet: 14 operations
- Financial Service: 18 operations
