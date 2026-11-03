# Realtime contract and recovery boundaries

The target transport schema is `contracts/asyncapi/beyvra-asyncapi-3.0.yaml`.
It declares thirteen channel families and an integer `schema_version: 1`; channel
names, payloads and authorization requirements come from that file. It is target
contract data, not proof of a deployed channel, durable history or working client.

Example of its generic event envelope (illustrative sequence, never a watermark):

```json
{
  "event_id": "event-example",
  "correlation_id": "correlation-example",
  "stream_id": "stream-example",
  "sequence": 1,
  "occurred_at": "2026-09-12T00:00:00Z",
  "event_type": "market.quote.updated.v1",
  "schema_version": 1,
  "data": {}
}
```

## Current V1 behavior

`FX/ws/realtime_views.py` retains authentication for ticket, snapshot and resume.
All three return 503 `REALTIME_AUTHORITY_UNAVAILABLE` until a real consuming
transport, authorized snapshot provider and ordered replay authority are bound.
Invalid negative/noninteger resume cursors return 400 `AFTER_SEQUENCE_INVALID`.
No usable ticket, fake sequence 1042 or empty successful replay is issued. Clients
must preserve their prior cursor, show unavailable state and retry with bounded
backoff; never reset to an invented watermark or discard missed events on 503.

## V2 and future recovery

`FX/ws/v2.py` owns the separate gated Centrifugo connection/subscription-token and
channel registry routes. Do not pass a V1 ticket to that gateway or treat its token
as a single-use V1 ticket. The target session route in AsyncAPI is not a claim that
V1 implements it. Confirm the exact deployed route and enabled authority first.

Once a durable history and snapshot binding are implemented and independently
certified, recovery must authorize the stream/account/tenant before replay, detect
cursor gaps, and bind snapshot state to a real per-stream watermark atomically.
A gap requires an authoritative snapshot; transport reconnect alone does not prove
that state is current. Those are remaining requirements, not implemented buffer,
409-gap response or snapshot guarantees on the V1 routes today.
