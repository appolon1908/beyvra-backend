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

## Executable request authority checks

Run `python -m unittest scripts.test_postman_authority` to compare each collection's
method/path inventory to its own OpenAPI document. OpenAPI server path prefixes
(`/api/v1` and the financial service's `/internal/v1`) are retained beneath the
local `base_url`; production server hosts are never copied into default targets.
Path parameters are Postman variables such as `{{watchlist_id}}`, initially blank.
Set test-fixture identifiers explicitly before any staging run.

The enterprise contract uses the `beyvra_access` cookie, not bearer authentication.
Supply its synthetic/local or separately authorized staging cookie via the blank
collection variable. The financial service requires client-certificate setup in
Postman/Newman outside the collection; a URL alone does not establish mutual TLS.
These tests validate derived request authority and do not execute API requests,
prove application behavior, or grant runtime/production certification.
