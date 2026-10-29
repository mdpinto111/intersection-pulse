from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DetectionViewSet, IngestView, IntersectionViewSet, health

router = DefaultRouter()
router.register("intersections", IntersectionViewSet)
router.register("detections", DetectionViewSet)

urlpatterns = [
    path("health/", health, name="health"),
    path("ingest/", IngestView.as_view(), name="ingest"),
    *router.urls,
]
