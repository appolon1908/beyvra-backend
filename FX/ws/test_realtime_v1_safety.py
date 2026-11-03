"""V1 must not certify a transport or replay cursor that does not exist."""

from types import SimpleNamespace

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from ws.realtime_views import (
    RealtimeResumeView,
    RealtimeSnapshotView,
    RealtimeTicketView,
)


class RealtimeUnavailableTests(SimpleTestCase):
    def test_authenticated_requests_never_receive_fabricated_success(self):
        factory = APIRequestFactory()
        for view, method, path in (
            (RealtimeTicketView, "post", "/api/v1/realtime/ticket"),
            (RealtimeSnapshotView, "get", "/api/v1/realtime/snapshot?topic=orders"),
            (RealtimeResumeView, "get", "/api/v1/realtime/resume?after_sequence=1041"),
        ):
            with self.subTest(path=path):
                request = getattr(factory, method)(path)
                force_authenticate(
                    request, SimpleNamespace(is_authenticated=True, pk=1, id=1)
                )
                response = view.as_view()(request)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(
                    response.data["error"]["code"], "REALTIME_AUTHORITY_UNAVAILABLE"
                )
                self.assertNotIn("ticket", response.data)
                self.assertNotIn("current_sequence", response.data)

    def test_authentication_is_still_required(self):
        response = RealtimeSnapshotView.as_view()(APIRequestFactory().get("/"))
        self.assertIn(response.status_code, (401, 403))
