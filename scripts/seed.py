"""
BusArrival AI - Database Seed Script
Fills all transit collections with realistic synthetic data:
- 7 Routes, 42 Stops, Route-Stops, 60 Days of Trips & Arrival Observations
- Rush-hour effects, day-type variations, congestion, rain shocks, and delay carry-over
- Deliberately messy rows (duplicates, outliers, negative delays, unmapped codes)
- Idempotent bulk_write upserts
- All records labeled "illustrative demo data"
Usage:
    python scripts/seed.py
    python scripts/seed.py --days 60 --db busarrival
"""

import sys
import argparse
from pathlib import Path

# Ensure repo root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_settings
from src.db.mongo import get_database, ensure_indexes, apply_collection_validators
from src.data.synthetic import generate_synthetic_dataset
from src.data.validate import validate_routes, validate_stops, validate_observations
from src.db.repositories.route_repo import RouteRepository, StopRepository, RouteStopRepository
from src.db.repositories.trip_repo import TripRepository
from src.db.repositories.observation_repo import ObservationRepository, DelayEventRepository
from src.db.repositories.audit_repo import AuditRepository


def run_seed(days: int = 60, seed_val: int = 42, db_name: str = None) -> dict:
    print(f"[*] Generating synthetic transit dataset ({days} days, seed={seed_val})...")
    data = generate_synthetic_dataset(num_days=days, seed=seed_val, include_messy_rows=True)

    db = get_database(db_name)
    print(f"[*] Applying collection validators and ensuring MongoDB indexes on '{db.name}'...")
    apply_collection_validators(db)
    ensure_indexes(db)

    route_repo = RouteRepository(db)
    stop_repo = StopRepository(db)
    route_stop_repo = RouteStopRepository(db)
    trip_repo = TripRepository(db)
    obs_repo = ObservationRepository(db)
    event_repo = DelayEventRepository(db)
    audit_repo = AuditRepository(db)

    print("[*] Validating generated dataset and detecting intentional messy rows...")
    valid_routes, r_issues = validate_routes(data["routes"])
    valid_stops, s_issues = validate_stops(data["stops"])

    route_set = {r["route_no"] for r in valid_routes}
    stop_set = {s["stop_code"] for s in valid_stops}

    valid_obs, obs_issues = validate_observations(
        data["observations"],
        valid_route_nos=route_set,
        valid_stop_codes=stop_set,
    )

    print(f"[!] Detected {len(obs_issues)} intentional messy/outlier rows in observations.")
    for issue in obs_issues[:5]:
        print(f"    - [Row {issue['row']}] {issue['field']}: {issue['message']}")

    print("[*] Performing idempotent bulk_write upserts across collections...")
    upserted_routes = route_repo.bulk_upsert_routes(valid_routes)
    upserted_stops = stop_repo.bulk_upsert_stops(valid_stops)
    upserted_route_stops = route_stop_repo.bulk_upsert_route_stops(data["route_stops"])
    upserted_trips = trip_repo.bulk_upsert_trips(data["trips"])
    upserted_obs = obs_repo.bulk_upsert_observations(valid_obs)
    upserted_events = event_repo.bulk_upsert_events(data["delay_events"])

    audit_repo.log_event(
        action="DATABASE_SEEDED",
        entity_type="system",
        details={
            "routes_count": len(valid_routes),
            "stops_count": len(valid_stops),
            "trips_count": len(data["trips"]),
            "observations_count": len(valid_obs),
            "detected_issues_count": len(obs_issues),
            "data_label": "illustrative demo data",
        },
    )

    summary = {
        "routes": len(valid_routes),
        "stops": len(valid_stops),
        "route_stops": len(data["route_stops"]),
        "trips": len(data["trips"]),
        "observations": len(valid_obs),
        "delay_events": len(data["delay_events"]),
        "detected_messy_issues": len(obs_issues),
    }

    print("\n[+] Database successfully seeded with illustrative demo data!")
    print(f"    - Routes: {summary['routes']}")
    print(f"    - Stops: {summary['stops']}")
    print(f"    - Route-Stops: {summary['route_stops']}")
    print(f"    - Trips: {summary['trips']}")
    print(f"    - Observations: {summary['observations']}")
    print(f"    - Delay Events: {summary['delay_events']}")
    print(f"    - Detected Messy Rows: {summary['detected_messy_issues']}")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed BusArrival AI Database")
    parser.add_argument("--days", type=int, default=60, help="Number of historical days to simulate (default: 60)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--db", type=str, help="Target database name (defaults to MONGODB_DB_NAME)")
    args = parser.parse_args()

    try:
        run_seed(days=args.days, seed_val=args.seed, db_name=args.db)
    except Exception as exc:
        print(f"[!] Seeding failed: {exc}", file=sys.stderr)
        sys.exit(1)
