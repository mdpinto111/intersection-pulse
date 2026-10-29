from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from traffic.models import Detection, Intersection
from traffic.services import congestion

INGEST_HEADERS = {"HTTP_X_INGEST_KEY": "test-key"}


@pytest.fixture(autouse=True)
def ingest_key(settings):
    settings.INGEST_API_KEY = "test-key"


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def intersection(db):
    return Intersection.objects.create(
        name="Ibn Gabirol / Arlozorov", city="Tel Aviv", latitude=32.0878, longitude=34.7819
    )


def make_detection(intersection, minutes_ago=1, **kwargs):
    defaults = dict(
        approach="N",
        vehicle_count=10,
        pedestrian_count=2,
        avg_speed_kmh=40,
        queue_length_m=10,
    )
    defaults.update(kwargs)
    return Detection.objects.create(
        intersection=intersection,
        observed_at=timezone.now() - timedelta(minutes=minutes_ago),
        **defaults,
    )


# --- congestion scoring -----------------------------------------------------

def test_congestion_free_flow_is_low():
    assert congestion(avg_speed_kmh=50, max_queue_m=0).level == "low"


def test_congestion_gridlock_is_high():
    c = congestion(avg_speed_kmh=0, max_queue_m=200)
    assert c.level == "high"
    assert c.score == 1.0


def test_congestion_without_data_is_low():
    assert congestion(None, None).score == 0.0


# --- health -------------------------------------------------------------------

@pytest.mark.django_db
def test_health(client):
    response = client.get("/api/health/")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"


# --- ingestion ----------------------------------------------------------------

def _payload(target, **overrides):
    item = {
        "intersection": target.id,
        "approach": "E",
        "observed_at": timezone.now().isoformat(),
        "vehicle_count": 12,
        "pedestrian_count": 3,
        "avg_speed_kmh": 32.5,
        "queue_length_m": 18,
    }
    item.update(overrides)
    return {"detections": [item]}


def test_ingest_requires_key(client, intersection):
    response = client.post("/api/ingest/", _payload(intersection), format="json")
    assert response.status_code == 403


def test_ingest_rejects_wrong_key(client, intersection):
    response = client.post(
        "/api/ingest/", _payload(intersection), format="json", HTTP_X_INGEST_KEY="nope"
    )
    assert response.status_code == 403


def test_ingest_creates_detections(client, intersection):
    response = client.post("/api/ingest/", _payload(intersection), format="json", **INGEST_HEADERS)
    assert response.status_code == 201
    assert response.json() == {"ingested": 1}
    assert Detection.objects.count() == 1


def test_ingest_validates_speed(client, intersection):
    response = client.post(
        "/api/ingest/", _payload(intersection, avg_speed_kmh=500), format="json", **INGEST_HEADERS
    )
    assert response.status_code == 400
    assert Detection.objects.count() == 0


def test_ingest_rejects_unknown_intersection(client, intersection):
    response = client.post(
        "/api/ingest/", _payload(intersection, intersection=9999), format="json", **INGEST_HEADERS
    )
    assert response.status_code == 400


# --- analytics ----------------------------------------------------------------

def test_stats_aggregates_per_approach(client, intersection):
    make_detection(intersection, approach="N", vehicle_count=10, avg_speed_kmh=40)
    make_detection(intersection, approach="N", vehicle_count=20, avg_speed_kmh=20)
    make_detection(intersection, approach="S", vehicle_count=5, queue_length_m=90, avg_speed_kmh=5)
    make_detection(intersection, minutes_ago=120, vehicle_count=999)  # outside window

    response = client.get(f"/api/intersections/{intersection.id}/stats/?minutes=15")
    assert response.status_code == 200
    body = response.json()

    assert body["total_vehicles"] == 35
    by_approach = {a["approach"]: a for a in body["approaches"]}
    assert by_approach["N"]["vehicles"] == 30
    assert by_approach["N"]["avg_speed_kmh"] == 30.0
    assert by_approach["S"]["congestion_level"] == "high"


def test_stats_rejects_invalid_window(client, intersection):
    response = client.get(f"/api/intersections/{intersection.id}/stats/?minutes=0")
    assert response.status_code == 400


def test_timeseries_buckets(client, intersection):
    for minutes_ago in (1, 2, 3, 30, 31):
        make_detection(intersection, minutes_ago=minutes_ago, vehicle_count=10)

    response = client.get(f"/api/intersections/{intersection.id}/timeseries/?minutes=60&bucket=60")
    assert response.status_code == 200
    points = response.json()["points"]
    assert sum(p["vehicles"] for p in points) == 50
    assert 1 <= len(points) <= 2  # one-hour buckets may straddle the hour boundary


def test_overview_includes_idle_intersections(client, intersection):
    idle = Intersection.objects.create(
        name="Begin / Kaplan", city="Tel Aviv", latitude=32.0735, longitude=34.7886
    )
    make_detection(intersection, vehicle_count=7)

    response = client.get("/api/intersections/overview/")
    assert response.status_code == 200
    data = {row["id"]: row for row in response.json()}
    assert data[intersection.id]["vehicles"] == 7
    assert data[idle.id]["vehicles"] == 0


def test_detections_filter_by_approach(client, intersection):
    make_detection(intersection, approach="N")
    make_detection(intersection, approach="W")
    response = client.get(f"/api/detections/?intersection={intersection.id}&approach=W")
    assert response.status_code == 200
    assert response.json()["count"] == 1
