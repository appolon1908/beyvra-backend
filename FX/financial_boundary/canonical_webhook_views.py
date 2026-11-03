import uuid
from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from financial_boundary.eventing import EventContractError
from financial_boundary.webhooks import (
    WebhookDenied,
    verify_provider_webhook,
)


DEFAULT_WEBHOOK_TENANT = uuid.uuid5(uuid.NAMESPACE_DNS, "beyvra-provider-webhooks")


class CanonicalProviderWebhookView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request, provider):
        # 1. Allowlist verification
        allowed_providers = {
            "alpaca",
            "drivewealth",
            "polygon",
            "coinbase",
            "simulated",
        }
        if provider not in allowed_providers:
            return Response({"error": {"code": "PROVIDER_DISALLOWED"}}, status=403)

        # 2. Body size limit (1MB max)
        if len(request.body) > 1024 * 1024:
            return Response({"error": {"code": "PAYLOAD_TOO_LARGE"}}, status=413)

        secret = getattr(settings, "PROVIDER_WEBHOOK_SECRET", None)
        if isinstance(secret, str):
            secret = secret.encode("utf-8")
        if not isinstance(secret, bytes) or len(secret) < 32:
            return Response(
                {"error": {"code": "WEBHOOK_AUTHORITY_UNAVAILABLE"}},
                status=503,
            )

        headers = {
            "X-Provider-Id": request.headers.get("X-Provider-Id", provider),
            "X-Event-Id": request.headers.get("X-Event-Id", ""),
            "X-Timestamp": request.headers.get("X-Timestamp", "0"),
            "X-Signature": request.headers.get("X-Signature", ""),
        }

        try:
            verify_provider_webhook(
                expected_provider_id=provider,
                tenant_ref=DEFAULT_WEBHOOK_TENANT,
                headers=headers,
                raw_body=request.body,
                secret=secret,
                replay_window_seconds=300,
            )
        except (WebhookDenied, EventContractError, OverflowError, OSError):
            return Response(
                {
                    "error": {
                        "code": "INVALID_WEBHOOK",
                        "message": "Webhook verification failed.",
                    }
                },
                status=401,
            )

        # No canonical execution handler/inbox is bound to this route yet.
        # Acknowledge nothing and write no deduplication marker: a provider
        # must be able to retry once durable domain processing is configured.
        return Response(
            {"error": {"code": "WEBHOOK_PROCESSING_UNAVAILABLE", "retryable": True}},
            status=503,
        )
