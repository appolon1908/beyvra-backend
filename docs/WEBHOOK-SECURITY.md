# Provider webhook security and processing boundary

`FX/financial_boundary/canonical_webhook_views.py` exposes the canonical execution
webhook route. It checks the provider allowlist, one-MiB body bound, configured
secret of at least 32 bytes, provider/event identity, timestamp and HMAC before
constructing a financial envelope. `financial_boundary.webhooks` owns verification.

The signature is HMAC-SHA256 over
`timestamp.event_id.provider_id.raw_body`, compared with `hmac.compare_digest`.
The timestamp window is inclusive: `abs(now - timestamp) <= 300` seconds. A valid
signature does not authorize an arbitrary provider, event shape or domain effect.

## Current response behavior

| Condition | Response | Domain processing |
|---|---|---|
| Disallowed provider | 403 `PROVIDER_DISALLOWED` | None |
| Body exceeds one MiB | 413 `PAYLOAD_TOO_LARGE` | None |
| Missing/short configured authority secret | 503 `WEBHOOK_AUTHORITY_UNAVAILABLE` | None |
| Invalid signature, replay timestamp or envelope | 401 `INVALID_WEBHOOK` | None |
| Authenticated, valid event with no bound canonical handler | 503 `WEBHOOK_PROCESSING_UNAVAILABLE` | None; no consumed marker |

The current route does not return 202 or 200-duplicate. It has no bound execution
handler or durable canonical inbox worker; a no-op handler would lose a real event.
Providers must retain retry eligibility. Do not suppress retries based on the
old fabricated accepted/duplicate response, and do not switch providers or invent
a new event identity to retry.

## Durable processing requirement

`financial_boundary.eventing.consume_financial_event` can atomically record the
`ProcessedEvent` marker and invoke a real handler. Its unique event UUID binds the
tenant, event type and payload hash; a conflicting replay raises
`EventReplayConflict`. Provider event UUIDs are derived from provider and event
identity. This is not a `(provider, external_id)` inbox table, and the function
is not yet bound to this route's execution effects.

Before enabling acknowledgments, bind and test the real tenant/account routing,
domain handler, durable processing/inbox policy, rollback behavior and duplicate
conflict handling. Only acknowledge after the declared durability boundary; no
accepted event may be discarded, and failures must remain retryable without
repeat domain effects. No provider or production activation is authorized here.
