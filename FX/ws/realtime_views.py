"""V1 realtime routes remain authenticated until a real transport is bound.

The V2 gateway has its own tokens and channel contract. A random V1 ticket
cannot be consumed by it, and the application outbox is not an ordered replay
log. Do not represent either as working V1 transport/history authority.
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


def _unavailable():
    return Response(
        {"error": {"code": "REALTIME_AUTHORITY_UNAVAILABLE", "retryable": True}},
        status=503,
    )


class RealtimeTicketView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        return _unavailable()


class RealtimeSnapshotView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return _unavailable()


class RealtimeResumeView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            after_sequence = int(request.query_params.get("after_sequence", "0"))
        except (TypeError, ValueError):
            after_sequence = -1
        if after_sequence < 0:
            return Response({"error": {"code": "AFTER_SEQUENCE_INVALID"}}, status=400)
        return _unavailable()
