from django.db import models


class Intersection(models.Model):
    """A signalized intersection equipped with sensors."""

    name = models.CharField(max_length=120)
    city = models.CharField(max_length=80)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["city", "name"]
        constraints = [
            models.UniqueConstraint(fields=["city", "name"], name="uniq_intersection_per_city"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.city})"


class Approach(models.TextChoices):
    NORTH = "N", "North"
    SOUTH = "S", "South"
    EAST = "E", "East"
    WEST = "W", "West"


class Detection(models.Model):
    """Aggregated sensor reading for one approach of an intersection.

    Each record summarizes a short sampling window (e.g. 10 seconds) as
    reported by the edge sensor.
    """

    intersection = models.ForeignKey(
        Intersection, on_delete=models.CASCADE, related_name="detections"
    )
    approach = models.CharField(max_length=1, choices=Approach.choices)
    observed_at = models.DateTimeField()
    vehicle_count = models.PositiveIntegerField()
    pedestrian_count = models.PositiveIntegerField(default=0)
    avg_speed_kmh = models.FloatField()
    queue_length_m = models.FloatField(default=0)

    class Meta:
        ordering = ["-observed_at"]
        indexes = [
            # Most queries are "readings of intersection X since T".
            models.Index(fields=["intersection", "observed_at"], name="det_inter_time_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.intersection_id}/{self.approach} @ {self.observed_at:%H:%M:%S}"
