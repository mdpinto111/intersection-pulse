from django.contrib import admin

from .models import Detection, Intersection


@admin.register(Intersection)
class IntersectionAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "is_active", "created_at")
    list_filter = ("city", "is_active")
    search_fields = ("name", "city")


@admin.register(Detection)
class DetectionAdmin(admin.ModelAdmin):
    list_display = ("intersection", "approach", "observed_at", "vehicle_count", "avg_speed_kmh")
    list_filter = ("approach", "intersection__city")
    date_hierarchy = "observed_at"
