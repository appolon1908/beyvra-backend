import json
import time
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory

from financial_boundary.canonical_webhook_views import CanonicalProviderWebhookView
from financial_boundary.webhooks import webhook_signature


class UnboundWebhookHandlerTests(SimpleTestCase):
    @override_settings(PROVIDER_WEBHOOK_SECRET=b"x" * 32)
    def test_verified_event_is_not_acknowledged_or_consumed_without_handler(self):
        now = int(time.time())
        body = json.dumps(
            {"event_type": "trade.execution", "order_id": "ord1"}
        ).encode()
        signature = webhook_signature(
            provider_id="alpaca",
            event_id="event_1001",
            timestamp=now,
            raw_body=body,
            secret=b"x" * 32,
        )
        request = APIRequestFactory().post(
            "/",
            body,
            content_type="application/json",
            HTTP_X_EVENT_ID="event_1001",
            HTTP_X_TIMESTAMP=str(now),
            HTTP_X_SIGNATURE=signature,
        )
        with patch("financial_boundary.webhooks.consume_financial_event") as consume:
            response = CanonicalProviderWebhookView.as_view()(
                request, provider="alpaca"
            )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.data["error"]["code"], "WEBHOOK_PROCESSING_UNAVAILABLE"
        )
        consume.assert_not_called()

    @override_settings(PROVIDER_WEBHOOK_SECRET=b"x" * 32)
    def test_signed_non_object_payload_is_rejected(self):
        now = int(time.time())
        body = b"[]"
        signature = webhook_signature(
            provider_id="alpaca",
            event_id="event_1002",
            timestamp=now,
            raw_body=body,
            secret=b"x" * 32,
        )
        request = APIRequestFactory().post(
            "/",
            body,
            content_type="application/json",
            HTTP_X_EVENT_ID="event_1002",
            HTTP_X_TIMESTAMP=str(now),
            HTTP_X_SIGNATURE=signature,
        )
        response = CanonicalProviderWebhookView.as_view()(request, provider="alpaca")
        self.assertEqual(response.status_code, 401)
