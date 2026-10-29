"""Edge-sensor simulator.

Stands in for the cameras/radars installed at each intersection: every
TICK_SECONDS it produces one reading per approach (N/S/E/W) for every active
intersection and pushes them in a single batch to the backend ingest API.

Traffic follows a daily curve with morning and evening rush hours, and an
occasional random "incident" saturates one approach for a few minutes so the
dashboard has something interesting to show.
"""
from __future__ import annotations

import asyncio
import logging
import math
import os
import random
import signal
from dataclasses import dataclass, field
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import httpx

API_URL = os.getenv("API_URL", "http://localhost:8000/api")
INGEST_API_KEY = os.getenv("INGEST_API_KEY", "dev-ingest-key")
TICK_SECONDS = float(os.getenv("TICK_SECONDS", "5"))
INCIDENT_PROBABILITY = float(os.getenv("INCIDENT_PROBABILITY", "0.01"))
# Rush hours follow the local time of the simulated city.
LOCAL_TZ = ZoneInfo(os.getenv("SIM_TIMEZONE", "Asia/Jerusalem"))
APPROACHES = ("N", "S", "E", "W")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("simulator")


def demand_factor(now: datetime) -> float:
    """Relative traffic demand (≈0.2 at night, ≈1.0 at rush hour)."""
    local = now.astimezone(LOCAL_TZ)
    hour = local.hour + local.minute / 60
    morning = math.exp(-((hour - 8.0) ** 2) / 2)
    evening = math.exp(-((hour - 17.5) ** 2) / 2.5)
    return 0.2 + 0.8 * max(morning, evening)


@dataclass
class ApproachState:
    """Per-approach state so consecutive readings evolve smoothly."""

    queue_m: float = 0.0
    incident_ticks_left: int = 0


@dataclass
class IntersectionSim:
    id: int
    base_volume: float  # vehicles per tick at full demand
    approaches: dict[str, ApproachState] = field(
        default_factory=lambda: {a: ApproachState() for a in APPROACHES}
    )

    def tick(self, now: datetime) -> list[dict]:
        demand = demand_factor(now)
        readings = []
        for approach, state in self.approaches.items():
            if state.incident_ticks_left == 0 and random.random() < INCIDENT_PROBABILITY:
                state.incident_ticks_left = random.randint(20, 60)
                log.info("incident started at intersection %s approach %s", self.id, approach)

            incident = state.incident_ticks_left > 0
            if incident:
                state.incident_ticks_left -= 1

            vehicles = max(0, round(random.gauss(self.base_volume * demand, 2)))
            # Queue grows with demand (or an incident) and drains otherwise.
            target_queue = 120 if incident else 70 * demand**2
            state.queue_m += (target_queue - state.queue_m) * 0.3 + random.uniform(-3, 3)
            state.queue_m = max(0.0, state.queue_m)

            speed = 50 * (1 - min(state.queue_m / 130, 0.95)) + random.uniform(-3, 3)

            readings.append(
                {
                    "intersection": self.id,
                    "approach": approach,
                    "observed_at": now.isoformat(),
                    "vehicle_count": vehicles if not incident else vehicles // 3,
                    "pedestrian_count": max(0, round(random.gauss(4 * demand, 1.5))),
                    "avg_speed_kmh": round(max(0.0, min(speed, 80.0)), 1),
                    "queue_length_m": round(state.queue_m, 1),
                }
            )
        return readings


async def fetch_intersections(client: httpx.AsyncClient) -> list[dict]:
    response = await client.get(f"{API_URL}/intersections/", params={"is_active": "true"})
    response.raise_for_status()
    return response.json()["results"]


async def push(client: httpx.AsyncClient, readings: list[dict]) -> None:
    """POST a batch with exponential backoff on transient failures."""
    for attempt in range(5):
        try:
            response = await client.post(
                f"{API_URL}/ingest/",
                json={"detections": readings},
                headers={"X-Ingest-Key": INGEST_API_KEY},
            )
            if response.status_code < 500:
                response.raise_for_status()  # 4xx = our bug, don't retry
                return
            log.warning("ingest returned %s, retrying", response.status_code)
        except httpx.TransportError as exc:
            log.warning("ingest unreachable (%s), retrying", exc)
        await asyncio.sleep(min(2**attempt, 30))
    log.error("dropping batch of %d readings after retries", len(readings))


async def wait_for_backend(client: httpx.AsyncClient) -> None:
    while True:
        try:
            if (await client.get(f"{API_URL}/health/")).status_code == 200:
                return
        except httpx.TransportError:
            pass
        log.info("waiting for backend at %s ...", API_URL)
        await asyncio.sleep(2)


async def run(stop: asyncio.Event) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        await wait_for_backend(client)
        sims: dict[int, IntersectionSim] = {}
        refresh_every = max(1, int(60 / TICK_SECONDS))  # pick up new intersections each minute
        tick = 0

        while not stop.is_set():
            if tick % refresh_every == 0:
                for item in await fetch_intersections(client):
                    sims.setdefault(item["id"], IntersectionSim(item["id"], random.uniform(8, 25)))

            now = datetime.now(timezone.utc)
            readings = [r for sim in sims.values() for r in sim.tick(now)]
            if readings:
                await push(client, readings)
                log.info("pushed %d readings for %d intersections", len(readings), len(sims))

            tick += 1
            try:
                await asyncio.wait_for(stop.wait(), timeout=TICK_SECONDS)
            except asyncio.TimeoutError:
                pass


def main() -> None:
    stop = asyncio.Event()
    loop = asyncio.new_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)  # graceful shutdown in containers
        except NotImplementedError:
            pass  # Windows: no signal handlers on the event loop, Ctrl+C still stops it
    loop.run_until_complete(run(stop))
    log.info("simulator stopped")


if __name__ == "__main__":
    main()
