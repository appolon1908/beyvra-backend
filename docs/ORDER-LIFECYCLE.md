# Canonical order lifecycle source contract

`FX/apps/trading/domain/orders.py` owns the `OrderState` enumeration and
`transition_order` validation. This table mirrors that source, including legacy
`PENDING` / `ACCEPTED` and both cancellation spellings; it is not evidence that
every view, worker or external provider has been integrated with that authority.

| Current state | Allowed next states |
|---|---|
| DRAFT | PREVIEWED, REJECTED |
| PREVIEWED | EXPIRED, PENDING_SUBMIT, REJECTED |
| PENDING_SUBMIT | ACCEPTED, ACKNOWLEDGED, REJECTED, UNKNOWN |
| PENDING | ACCEPTED, ACKNOWLEDGED, REJECTED, UNKNOWN |
| ACCEPTED | ACKNOWLEDGED, CANCEL_PENDING, OPEN |
| ACKNOWLEDGED | CANCEL_PENDING, EXPIRED, FILLED, OPEN, PARTIALLY_FILLED |
| OPEN | CANCEL_PENDING, EXPIRED, FILLED, PARTIALLY_FILLED |
| PARTIALLY_FILLED | CANCEL_PENDING, FILLED, PARTIALLY_FILLED |
| FILLED | (terminal) |
| CANCEL_PENDING | CANCELED, CANCELLED |
| CANCELLED | (terminal) |
| CANCELED | (terminal) |
| REJECTED | (terminal) |
| EXPIRED | (terminal) |
| UNKNOWN | ACKNOWLEDGED, CANCELED, CANCELLED, FILLED, RECONCILIATION_REQUIRED, REJECTED |
| RECONCILIATION_REQUIRED | ACKNOWLEDGED, CANCELED, CANCELLED, FILLED, REJECTED |

## Transaction and authorization requirements

A legal state transition alone does not authorize a financial operation. Validate
tenant/account ownership, freshness, compliance, risk, idempotency and reservation
authority through the existing services before applying a protected transition.
Persist state, immutable audit/event and outbox intent within their canonical
transaction boundary; do not create a duplicate balance or reservation engine.
The exact policy controls the quote-age limit, not an unconditional 1500ms claim
from this document.

`UNKNOWN` and `RECONCILIATION_REQUIRED` permit several transitions in the graph,
but they require authoritative matching evidence and the reviewed reconciliation
policy. A timeout or missing provider lookup cannot authorize rejection, funds
release, failover or resend. See `ORDER-UNKNOWN-OUTCOME-RUNBOOK.md`.

Source contract tests and local reconciliation do not certify live routing,
financial effects, provider state or production readiness. Existing safety flags,
authentication, tenant boundaries and release gates remain required.
