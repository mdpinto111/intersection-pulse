from datetime import datetime, timezone

from simulator import LOCAL_TZ, IntersectionSim, demand_factor


def test_rush_hour_has_more_demand_than_night():
    rush = demand_factor(datetime(2026, 1, 1, 8, 0, tzinfo=LOCAL_TZ))
    night = demand_factor(datetime(2026, 1, 1, 3, 0, tzinfo=LOCAL_TZ))
    assert rush > 0.9
    assert night < 0.3


def test_tick_produces_valid_reading_per_approach():
    sim = IntersectionSim(id=1, base_volume=15)
    readings = sim.tick(datetime.now(timezone.utc))
    assert {r["approach"] for r in readings} == {"N", "S", "E", "W"}
    for r in readings:
        assert r["vehicle_count"] >= 0
        assert 0 <= r["avg_speed_kmh"] <= 80
        assert r["queue_length_m"] >= 0
