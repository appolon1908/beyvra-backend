# Backend Production Completion Map

This is a source inventory, not a production completion certificate. It records the
implementation present after reconciling the platform API with current `main`.
Listed migrations are source files, not proof that a database has applied them.

## Source authorities

| Domain | Existing source authority | Existing migration file |
|---|---|---|
| Platform configuration and capabilities | `FX/platform_ops/platform_api.py`; `HealthAuthority` in `FX/platform_ops/health/services.py`; simulation availability in `FX/apps/trading/application/simulation.py` | `FX/platform_ops/migrations/0003_complete_sli_inventory.py` |
| Order management | `TradingOrder` in `FX/apps/trading/models.py`; `FX/apps/trading/api/views.py`; simulation and account services in `FX/apps/trading/application/` | `FX/apps/trading/migrations/0011_account_identity_boundary.py` |
| Financial event boundary | `FinancialOutboxEvent`, `DeadLetterEvent`, `FinancialProjectionCursor` in `FX/financial_boundary/models.py`; `eventing.py`, `reconciliation.py`, `halts.py` in that package | `FX/financial_boundary/migrations/0005_financial_halt_authority.py` |
| Reference data | `Instrument`, `InstrumentVersion`, `ProviderSymbolMapping` in `FX/reference_data/models.py`; `resolve_provider_symbol` in `FX/reference_data/services.py` | `FX/reference_data/migrations/0002_immutable_lineage.py` |
| Pricing entitlements | `FX/pricing_authority/models.py`; `FX/pricing_authority/urls.py` | `FX/pricing_authority/migrations/0002_tenant_scoped_entitlements.py` |
| Watchlists | `Watchlist`, `WatchlistItem` in `FX/apps/workspace/models.py`; `FX/apps/workspace/api.py` | `FX/apps/workspace/migrations/0001_initial.py` |
| Compliance | `FX/apps/compliance/models.py`; `get_trading_eligibility` in `FX/apps/compliance/services.py` | `FX/apps/compliance/migrations/0014_override_constraints.py` |
| Foundation events and audit | `OutboxEvent`, `ProcessedEvent`, `IdempotencyRecord`, `ApplicationAuditEvent`, `TradingControl` in `FX/apps/foundation/models.py`; `FX/apps/foundation/services.py` | `FX/apps/foundation/migrations/0002_audit_append_only.py` |

The original map's proposed `PlatformConfig`, `TenantEntitlement`, `FinancialLedger`,
`FinancialReservation`, `WebhookInbox`, and `WebhookDeadLetter` authorities are not
established by this source inventory. Do not create duplicate authorities to match
those names. In particular, this PR does not implement the later canonical order,
account, market snapshot, realtime ticket/resume, or provider webhook milestones.

## Platform API boundary

- `FX/FX/urls.py` mounts `platform_ops.platform_urls` at `/api/v1/platform/`.
- `GET /api/v1/platform/config` exposes public configuration using the existing safety-state authority.
- `GET /api/v1/platform/capabilities` supports optional session-bound authentication; compliance queries use the resolved tenant context and do not persist an eligibility decision.
- Provider health requires the existing operator authorization check; being ordinary staff alone does not grant access.
- Conditional responses retain private, no-store cache policy. An unhealthy system disables simulation availability.
- Source inventory does not prove tenant isolation or idempotency for every other API. Those require their own tests and exact-revision evidence.

## Verification and release boundaries

Platform regression entry point: `FX/platform_ops/tests/test_platform_capabilities_api.py`.
Related suites live under `FX/apps/trading/tests/`, `FX/financial_boundary/tests/`,
`FX/apps/compliance/tests.py`, and `FX/apps/valuation/`.

Production and staging activation remain unauthorized. Keep existing safety defaults,
authentication, authorization, migration checks, security scans, and release gates.
A clean source merge or local unit suite does not prove PostgreSQL migration state,
provider integration, load behavior, hosted CI completion, or production readiness.
