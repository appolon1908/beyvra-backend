# Order unknown outcome runbook

A timeout, disconnect, missing response or an absent provider lookup is not proof
of rejection. Preserve `UNKNOWN` / `RECONCILIATION_REQUIRED`, the original client
identity, operation reference, reservation and evidence. Freeze automatic resend
and failover for that attempt; never create a replacement order to probe its state.

1. Identify the tenant, account, immutable candidate, original client identity and
   attempt. Inspect canonical order/execution records and read-only provider
   evidence through the approved adapter. Do not expose credentials or raw PII.
2. A provider `not found` / `unknown` result may be eventual consistency or a
   limited lookup scope. Keep the outcome unknown and the reservation held. Do not
   transition to `REJECTED`, release funds or resend based only on missing lookup.
3. An authoritative accepted/fill/cancellation/rejection result must match the
   original identity, account, quantity and scope. Apply it only through the
   existing reviewed reconciliation/state authority and deduplicated transaction.
   Terminal resolution or reservation release requires positive final evidence
   and the existing authorization policy; a signed operator note alone cannot
   replace provider or canonical financial evidence.
4. Repeated inconclusive reads, inconsistent records, unavailable adapters or an
   exhausted approved retry budget require operator escalation. No five-attempt
   or five-minute budget is asserted by this document; use the configured and
   reviewed policy. Keep safety holds while the investigation continues.
5. Preserve the original unknown record, evidence references, transition and audit
   outcome. Verify domain/financial projections before resolving the incident.

`FX/apps/trading/execution_control/reconciliation.py` provides local inspection
checks; it does not query a provider or establish provider absence.
`python manage.py run_reconciliation --scope full --format json --no-persist`
performs read-only simulated-trading reconciliation. A local PASS is not proof of
an external outcome. No general force-resolution CLI is certified here.
