"""Traffic analytics.

Kept separate from the views so the business rules can be unit-tested
without HTTP and reused by other entry points (admin, management commands).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db.models import Avg, Count, Max, Sum
from django.db.models.functions import TruncMinute
from django.utils import timezone

from .models import Detection

# Above this queue length (meters) an approach is considered saturated.
QUEUE_SATURATION_M = 80.0
# Free-flow speed for an urban approach (km/h).
FREE_FLOW_SPEED_KMH = 50.0


@dataclass(frozen=True)
class Congestion:
    score: float  # 0 (free flow) .. 1 (gridlock)
    level: str  # "low" | "moderate" | "high"


def congestion(avg_speed_kmh: float | None, max_queue_m: float | None) -> Congestion:
    """Blend queue length and speed drop into a single 0..1 score."""
    if avg_speed_kmh is None or max_queue_m is None:
        return Congestion(score=0.0, level="low")

    queue_factor = min(max_queue_m / QUEUE_SATURATION_M, 1.0)
    speed_factor = max(0.0, 1.0 - avg_speed_kmh / FREE_FLOW_SPEED_KMH)
    score = round(0.6 * queue_factor + 0.4 * speed_factor, 3)

    if score < 0.33:
        level = "low"
    elif score < 0.66:
        level = "moderate"
    else:
        level = "high"
    return Congestion(score=score, level=level)


def window_start(minutes: int, now: datetime | None = None) -> datetime:
    return (now or timezone.now()) - timedelta(minutes=minutes)


def intersection_stats(intersection_id: int, minutes: int) -> dict:
    """Per-approach and overall statistics over the last `minutes`."""
    qs = Detection.objects.filter(
        intersection_id=intersection_id, observed_at__gte=window_start(minutes)
    )

    rows = (
        qs.values("approach")
        .annotate(
            vehicles=Sum("vehicle_count"),
            pedestrians=Sum("pedestrian_count"),
            avg_speed=Avg("avg_speed_kmh"),
            max_queue=Max("queue_length_m"),
            samples=Count("id"),
        )
        .order_by("approach")
    )

    approaches = []
    for row in rows:
        c = congestion(row["avg_speed"], row["max_queue"])
        approaches.append(
            {
                "approach": row["approach"],
                "vehicles": row["vehicles"] or 0,
                "pedestrians": row["pedestrians"] or 0,
                "avg_speed_kmh": round(row["avg_speed"] or 0, 1),
                "max_queue_m": round(row["max_queue"] or 0, 1),
                "samples": row["samples"],
                "congestion_score": c.score,
                "congestion_level": c.level,
            }
        )

    overall = qs.aggregate(
        vehicles=Sum("vehicle_count"),
        avg_speed=Avg("avg_speed_kmh"),
        max_queue=Max("queue_length_m"),
    )
    c = congestion(overall["avg_speed"], overall["max_queue"])

    return {
        "intersection_id": intersection_id,
        "window_minutes": minutes,
        "total_vehicles": overall["vehicles"] or 0,
        "avg_speed_kmh": round(overall["avg_speed"] or 0, 1),
        "congestion_score": c.score,
        "congestion_level": c.level,
        "approaches": approaches,
    }


def intersection_timeseries(intersection_id: int, minutes: int, bucket_minutes: int) -> list[dict]:
    """Vehicle volume and speed grouped in buckets of `bucket_minutes`.

    The database does the heavy lifting at minute granularity (TruncMinute);
    the minute rows are then folded into wider buckets in Python, which keeps
    the query portable across SQLite (tests) and PostgreSQL (production).
    """
    per_minute = (
        Detection.objects.filter(
            intersection_id=intersection_id, observed_at__gte=window_start(minutes)
        )
        .annotate(minute=TruncMinute("observed_at"))
        .values("minute")
        .annotate(vehicles=Sum("vehicle_count"), speed=Avg("avg_speed_kmh"), n=Count("id"))
        .order_by("minute")
    )

    bucket_seconds = bucket_minutes * 60
    buckets: dict[int, dict] = defaultdict(lambda: {"vehicles": 0, "speed_sum": 0.0, "n": 0})
    for row in per_minute:
        key = int(row["minute"].timestamp()) // bucket_seconds * bucket_seconds
        b = buckets[key]
        b["vehicles"] += row["vehicles"] or 0
        b["speed_sum"] += (row["speed"] or 0) * row["n"]
        b["n"] += row["n"]

    tz = timezone.get_current_timezone()
    return [
        {
            "bucket_start": datetime.fromtimestamp(key, tz=tz).isoformat(),
            "vehicles": b["vehicles"],
            "avg_speed_kmh": round(b["speed_sum"] / b["n"], 1) if b["n"] else 0,
        }
        for key, b in sorted(buckets.items())
    ]


def network_overview(minutes: int) -> dict[int, dict]:
    """Current congestion for every intersection in a single grouped query."""
    rows = (
        Detection.objects.filter(observed_at__gte=window_start(minutes))
        .values("intersection_id")
        .annotate(
            vehicles=Sum("vehicle_count"),
            avg_speed=Avg("avg_speed_kmh"),
            max_queue=Max("queue_length_m"),
        )
    )
    result = {}
    for row in rows:
        c = congestion(row["avg_speed"], row["max_queue"])
        result[row["intersection_id"]] = {
            "vehicles": row["vehicles"] or 0,
            "avg_speed_kmh": round(row["avg_speed"] or 0, 1),
            "congestion_score": c.score,
            "congestion_level": c.level,
        }
    return result
