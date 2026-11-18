"""
Seed Madurai City Bus Transit Data into MongoDB Atlas.
Inserts routes, stops, route_stops, and observations for Madurai.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.db.mongo import get_database
from src.db.repositories.route_repo import RouteRepository, StopRepository, RouteStopRepository
from src.db.repositories.observation_repo import ObservationRepository
from scripts.generate_madurai_data import ROUTES, STOPS, ROUTE_STOPS, generate_observations

def seed_madurai():
    db = get_database()
    print(f"Connecting to database: {db.name}...")

    route_repo = RouteRepository(db)
    stop_repo = StopRepository(db)
    rs_repo = RouteStopRepository(db)
    obs_repo = ObservationRepository(db)

    # 1. Upsert Routes
    n_routes = route_repo.bulk_upsert_routes(ROUTES)
    print(f"✓ Upserted {n_routes} Madurai routes: {[r['route_no'] for r in ROUTES]}")

    # 2. Upsert Stops
    n_stops = stop_repo.bulk_upsert_stops(STOPS)
    print(f"✓ Upserted {n_stops} Madurai stops across Periyar, Goripalayam, Airport, Mattuthavani...")

    # 3. Upsert Route Stops
    n_rs = rs_repo.bulk_upsert_route_stops(ROUTE_STOPS)
    print(f"✓ Upserted {n_rs} Madurai route-stop sequence links")

    # 4. Upsert Observations with datetime types for MongoDB schema validation
    raw_observations = generate_observations()
    parsed_observations = []
    for o in raw_observations:
        doc = dict(o)
        if isinstance(doc["scheduled_arrival"], str):
            doc["scheduled_arrival"] = datetime.strptime(doc["scheduled_arrival"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        if isinstance(doc["actual_arrival"], str):
            doc["actual_arrival"] = datetime.strptime(doc["actual_arrival"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        parsed_observations.append(doc)

    n_obs = obs_repo.bulk_upsert_observations(parsed_observations)
    print(f"✓ Upserted {n_obs} Madurai arrival observations for model training & testing")

    print("\n🎉 Madurai City Transit Data seeded successfully into database!")

if __name__ == "__main__":
    seed_madurai()
