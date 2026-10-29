from rest_framework import serializers

from .models import Detection, Intersection


class IntersectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Intersection
        fields = ["id", "name", "city", "latitude", "longitude", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class DetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Detection
        fields = [
            "id",
            "intersection",
            "approach",
            "observed_at",
            "vehicle_count",
            "pedestrian_count",
            "avg_speed_kmh",
            "queue_length_m",
        ]
        read_only_fields = ["id"]

    def validate_avg_speed_kmh(self, value):
        if not 0 <= value <= 200:
            raise serializers.ValidationError("Speed must be between 0 and 200 km/h.")
        return value

    def validate_queue_length_m(self, value):
        if value < 0:
            raise serializers.ValidationError("Queue length cannot be negative.")
        return value


class IngestSerializer(serializers.Serializer):
    """Batch of detections pushed by an edge sensor / the simulator."""

    detections = DetectionSerializer(many=True, allow_empty=False)

    def validate_detections(self, value):
        if len(value) > 1000:
            raise serializers.ValidationError("At most 1000 detections per batch.")
        return value


class WindowQuerySerializer(serializers.Serializer):
    minutes = serializers.IntegerField(min_value=1, max_value=24 * 60, default=15)
    bucket = serializers.IntegerField(min_value=1, max_value=60, default=5)
