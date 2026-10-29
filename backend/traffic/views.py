import logging

from django.db import connection, transaction
from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import Detection, Intersection
from .permissions import HasIngestKey
from .serializers import (
    DetectionSerializer,
    IngestSerializer,
    IntersectionSerializer,
    WindowQuerySerializer,
)

logger = logging.getLogger(__name__)


class IntersectionViewSet(viewsets.ModelViewSet):
    queryset = Intersection.objects.all()
    serializer_class = IntersectionSerializer
    filterset_fields = ["city", "is_active"]

    def _window(self, request):
        params = WindowQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        return params.validated_data

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        intersection = self.get_object()
        window = self._window(request)
        return Response(services.intersection_stats(intersection.id, window["minutes"]))

    @action(detail=True, methods=["get"])
    def timeseries(self, request, pk=None):
        intersection = self.get_object()
        window = self._window(request)
        data = services.intersection_timeseries(
            intersection.id, window["minutes"], window["bucket"]
        )
        return Response({"intersection_id": intersection.id, **window, "points": data})

    @action(detail=False, methods=["get"])
    def overview(self, request):
        """All active intersections with their live congestion, for the map view."""
        window = self._window(request)
        live = services.network_overview(window["minutes"])
        empty = {
            "vehicles": 0,
            "avg_speed_kmh": 0,
            "congestion_score": 0,
            "congestion_level": "low",
        }
        payload = [
            {**IntersectionSerializer(i).data, **live.get(i.id, empty)}
            for i in Intersection.objects.filter(is_active=True)
        ]
        return Response(payload)


class DetectionFilter(filters.FilterSet):
    since = filters.IsoDateTimeFilter(field_name="observed_at", lookup_expr="gte")
    until = filters.IsoDateTimeFilter(field_name="observed_at", lookup_expr="lt")

    class Meta:
        model = Detection
        fields = ["intersection", "approach"]


class DetectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Detection.objects.select_related("intersection")
    serializer_class = DetectionSerializer
    filterset_class = DetectionFilter


class IngestView(APIView):
    """Bulk ingestion endpoint used by the sensor simulator microservice."""

    permission_classes = [HasIngestKey]

    def post(self, request):
        serializer = IngestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rows = [Detection(**item) for item in serializer.validated_data["detections"]]
        with transaction.atomic():
            Detection.objects.bulk_create(rows, batch_size=500)
        logger.info("ingested %d detections", len(rows))
        return Response({"ingested": len(rows)}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """Liveness + DB readiness probe for the container orchestrator."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return Response({"status": "ok", "database": "ok"})
    except Exception:  # pragma: no cover - only hit when the DB is down
        logger.exception("health check failed")
        return Response(
            {"status": "degraded", "database": "unreachable"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
