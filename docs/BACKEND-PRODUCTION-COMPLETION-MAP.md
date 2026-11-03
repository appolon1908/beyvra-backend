# Backend Production Completion Map

This is a source inventory, not a production completion certificate. It records the
implementation present on this stacked B10 branch.
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
those names. Canonical milestone modules on this branch include
`FX/apps/trading/api/views.py`,
`FX/apps/trading/api/account_projections_views.py`,
`FX/reference_data/market_data_views.py`, `FX/ws/realtime_views.py`, and
`FX/financial_boundary/canonical_webhook_views.py`. Module presence alone does
not establish working end-to-end integration.

V1 realtime tickets, snapshots and replay deliberately return 503 because no
consuming transport or durable ordered replay authority is bound. Verified
provider webhooks return 503 without recording a consumed marker because no
canonical execution handler is bound. Neither route is production-complete.

## Route and data boundaries

`FX/FX/urls.py` mounts platform configuration, canonical market, realtime and
provider webhook views. Route presence does not certify permissions, provider
integration, or frontend behavior. The canonical market views return finite,
explicitly simulated fixtures, not live provider data or replayable market history.
The existing platform capabilities implementation on this branch still requires
its own security and tenant review; newer main corrections are not implied here.

## Verification and release boundaries

Platform regression entry point: `FX/platform_ops/tests/test_platform_capabilities_api.py`.
Related suites live under `FX/apps/trading/tests/`, `FX/financial_boundary/tests/`,
`FX/apps/compliance/tests.py`, and `FX/apps/valuation/`.

Production and staging activation remain unauthorized. Keep existing safety defaults,
authentication, authorization, migration checks, security scans, and release gates.
A clean source merge or local unit suite does not prove PostgreSQL migration state,
provider integration, load behavior, hosted CI completion, or production readiness.
