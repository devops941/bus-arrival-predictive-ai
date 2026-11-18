"""
BusArrival AI - Synthetic Transit Data Generator
Generates realistic multi-route transit datasets with:
- Rush-hour peaks (morning 07:30-09:30, evening 16:30-19:00)
- Day-type variations (weekday, weekend, holiday)
- Route-specific corridor congestion
- Weather shocks (rain flag with delay spikes)
- Downstream delay carry-over (compounding delays from stop to stop)
- Deliberately messy rows (duplicates, negative/absurd delays, missing stop, unknown route)
All data explicitly labeled "illustrative demo data".
"""

from datetime import datetime, date, time, timedelta, timezone
import random
import math
from typing import Dict, Any, List, Tuple


DEMO_LABEL = "illustrative demo data"


# Realistic route specifications
ROUTES_SPEC = [
    {"route_no": "101", "name": "Metro Express", "origin": "Central Station", "destination": "North Terminal", "total_distance_km": 18.5, "scheduled_headway_min": 15},
    {"route_no": "204", "name": "University Shuttle", "origin": "Campus West", "destination": "Downtown Hub", "total_distance_km": 12.0, "scheduled_headway_min": 20},
    {"route_no": "305", "name": "Airport Direct", "origin": "City Center", "destination": "Terminal 2", "total_distance_km": 28.0, "scheduled_headway_min": 30},
    {"route_no": "408", "name": "Crosstown Link", "origin": "East Park", "destination": "Westridge Mall", "total_distance_km": 15.2, "scheduled_headway_min": 20},
    {"route_no": "512", "name": "Harbor Line", "origin": "Ferry Wharf", "destination": "Tech District", "total_distance_km": 10.4, "scheduled_headway_min": 15},
    {"route_no": "610", "name": "Suburban Loop", "origin": "North Station", "destination": "Suburban Center", "total_distance_km": 22.0, "scheduled_headway_min": 30},
    {"route_no": "720", "name": "Night Owl Transit", "origin": "Grand Central", "destination": "South Gate", "total_distance_km": 16.8, "scheduled_headway_min": 45},
]

# Stop templates around a metropolitan area (center lat: 12.9716, lon: 77.5946)
BASE_STOPS = [
    ("ST-001", "Central Station", 12.9716, 77.5946),
    ("ST-002", "Commerce Square", 12.9750, 77.5990),
    ("ST-003", "Victoria Hospital", 12.9630, 77.5750),
    ("ST-004", "Tech Park East", 12.9850, 77.6350),
    ("ST-005", "Metro Junction", 12.9780, 77.6100),
    ("ST-006", "University Gate", 12.9350, 77.5350),
    ("ST-007", "Science Center", 12.9420, 77.5450),
    ("ST-008", "Downtown Library", 12.9720, 77.6010),
    ("ST-009", "Market Road", 12.9650, 77.5850),
    ("ST-010", "North Terminal", 13.0150, 77.5920),
    ("ST-011", "Airport Plaza", 13.1980, 77.7060),
    ("ST-012", "Terminal 1", 13.2010, 77.7100),
    ("ST-013", "Terminal 2", 13.2040, 77.7150),
    ("ST-014", "East Park", 12.9800, 77.6600),
    ("ST-015", "Westridge Mall", 12.9600, 77.5100),
    ("ST-016", "Greenfield Ave", 12.9550, 77.5250),
    ("ST-017", "Ferry Wharf", 12.9400, 77.6200),
    ("ST-018", "Tech District 4", 12.9300, 77.6900),
    ("ST-019", "Suburban Center", 13.0400, 77.5600),
    ("ST-020", "South Gate Interchange", 12.9100, 77.5800),
    ("ST-021", "Civic Center", 12.9730, 77.5910),
    ("ST-022", "Highland Park", 12.9900, 77.5800),
    ("ST-023", "Sunset Blvd", 12.9500, 77.5500),
    ("ST-024", "Riverfront", 12.9350, 77.6150),
    ("ST-025", "Stadium Road", 12.9810, 77.6050),
    ("ST-026", "Industrial Way", 12.9150, 77.6400),
    ("ST-027", "Old Town Square", 12.9670, 77.5790),
    ("ST-028", "Grand Avenue", 12.9760, 77.5880),
    ("ST-029", "Pine Street", 12.9830, 77.5950),
    ("ST-030", "Oak Ridge", 13.0020, 77.5700),
    ("ST-031", "Valley View", 12.9200, 77.5600),
    ("ST-032", "Lakeside Pier", 12.9450, 77.6300),
    ("ST-033", "Hillcrest", 12.9950, 77.6200),
    ("ST-034", "Boulevard West", 12.9580, 77.5300),
    ("ST-035", "Exchange Place", 12.9700, 77.6080),
    ("ST-036", "Botanical Gardens", 12.9500, 77.5850),
    ("ST-037", "Broad Street", 12.9620, 77.5970),
    ("ST-038", "Millennium Tower", 12.9880, 77.6400),
    ("ST-039", "Outer Ring Road 1", 12.9250, 77.6700),
    ("ST-040", "Outer Ring Road 2", 12.9380, 77.6850),
    ("ST-041", "Northridge", 13.0250, 77.5800),
    ("ST-042", "Southridge", 12.9000, 77.5700),
]


def generate_synthetic_dataset(
    num_days: int = 60,
    seed: int = 42,
    include_messy_rows: bool = True
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate synthetic transit dataset for demonstration and benchmarking.
    Returns:
      routes, stops, route_stops, trips, observations, delay_events
    """
    random.seed(seed)
    created_at = datetime.now(timezone.utc)

    # 1. Routes
    routes = []
    for r in ROUTES_SPEC:
        route_doc = dict(r)
        route_doc["active"] = True
        route_doc["data_label"] = DEMO_LABEL
        route_doc["created_at"] = created_at
        routes.append(route_doc)

    # 2. Stops
    stops = []
    for code, name, lat, lon in BASE_STOPS:
        stops.append({
            "stop_code": code,
            "name": name,
            "lat": lat,
            "lon": lon,
            "data_label": DEMO_LABEL,
            "created_at": created_at,
        })

    # 3. Route-Stops (Allocate 6-8 stops per route)
    route_stops = []
    for r_idx, r in enumerate(routes):
        # Pick 6 to 8 stops sequentially
        start_idx = (r_idx * 4) % (len(stops) - 8)
        selected_stops = stops[start_idx : start_idx + random.randint(6, 8)]
        total_dist = r["total_distance_km"]
        step_dist = total_dist / (len(selected_stops) - 1)
        total_time_min = total_dist * 2.2  # ~27 km/h avg scheduled speed

        for seq, st in enumerate(selected_stops, start=1):
            dist_from_start = round(seq * step_dist - step_dist, 2)
            offset_min = int(round((seq - 1) * (total_time_min / (len(selected_stops) - 1))))
            route_stops.append({
                "route_no": r["route_no"],
                "stop_code": st["stop_code"],
                "sequence": seq,
                "distance_from_start_km": dist_from_start,
                "scheduled_offset_min": offset_min,
                "data_label": DEMO_LABEL,
                "created_at": created_at,
            })

    # 4. Trips & Observations
    start_date = date.today() - timedelta(days=num_days)
    trips = []
    observations = []
    delay_events = []
    trip_counter = 1

    # Daily trip start times (hours)
    departure_hours = [6, 7, 8, 9, 11, 13, 15, 17, 18, 19, 21]

    for d in range(num_days):
        current_date = start_date + timedelta(days=d)
        is_weekend = current_date.weekday() >= 5
        day_type = "weekend" if is_weekend else "weekday"
        
        # 10% chance of rain shock on any day
        rain_shock = random.random() < 0.12

        if rain_shock:
            delay_events.append({
                "date": current_date.isoformat(),
                "time": "16:00:00",
                "route_no": "101",
                "cause": "rain",
                "minutes": 15,
                "data_label": DEMO_LABEL,
                "created_at": created_at,
            })

        for r in routes:
            r_no = r["route_no"]
            r_stops = [rs for rs in route_stops if rs["route_no"] == r_no]
            r_stops.sort(key=lambda x: x["sequence"])

            # Schedule trips across day
            for dep_hour in departure_hours:
                if is_weekend and dep_hour in (6, 21):
                    continue  # fewer trips on weekend

                trip_id = f"TR-{r_no}-{current_date.strftime('%Y%m%d')}-{dep_hour:02d}00"
                sched_start = datetime.combine(
                    current_date,
                    time(hour=dep_hour, minute=0, second=0)
                ).replace(tzinfo=timezone.utc)

                vehicle_id = f"BUS-{r_no}-{random.randint(10, 99)}"
                trips.append({
                    "trip_id": trip_id,
                    "route_no": r_no,
                    "direction": "outbound",
                    "date": current_date.isoformat(),
                    "scheduled_start": sched_start,
                    "vehicle_id": vehicle_id,
                    "day_type": day_type,
                    "data_label": DEMO_LABEL,
                    "created_at": created_at,
                })

                # Determine base trip delay characteristics
                is_morning_rush = (7 <= dep_hour <= 9) and not is_weekend
                is_evening_rush = (16 <= dep_hour <= 19) and not is_weekend

                accumulated_delay = 0.0
                if is_morning_rush:
                    accumulated_delay += random.uniform(3.0, 8.0)
                elif is_evening_rush:
                    accumulated_delay += random.uniform(4.0, 10.0)
                else:
                    accumulated_delay += random.uniform(-1.0, 2.5)

                if rain_shock:
                    accumulated_delay += random.uniform(4.0, 9.0)

                # Generate arrival observation for each stop along the trip
                for rs in r_stops:
                    offset = timedelta(minutes=rs["scheduled_offset_min"])
                    sched_arrival = sched_start + offset

                    # Delay carry-over with slight additive random walk
                    step_noise = random.gauss(0.2, 0.6)
                    accumulated_delay = max(-2.0, accumulated_delay + step_noise)

                    actual_arrival = sched_arrival + timedelta(minutes=accumulated_delay)
                    delay_min = round((actual_arrival - sched_arrival).total_seconds() / 60.0, 2)

                    passengers = random.randint(15, 65) if (is_morning_rush or is_evening_rush) else random.randint(5, 30)
                    weather = "Rain" if rain_shock else "Clear"

                    observations.append({
                        "trip_id": trip_id,
                        "stop_code": rs["stop_code"],
                        "route_no": r_no,
                        "scheduled_arrival": sched_arrival,
                        "actual_arrival": actual_arrival,
                        "delay_min": delay_min,
                        "passengers_optional": passengers,
                        "weather_optional": weather,
                        "is_outlier": False,
                        "data_label": DEMO_LABEL,
                        "created_at": created_at,
                    })

    # Deliberately messy rows to verify validation rules (Section 5)
    if include_messy_rows and observations:
        # 1. Duplicate row with identical (trip_id, stop_code)
        dup_row = dict(observations[0])
        dup_row["delay_min"] += 1.5
        observations.append(dup_row)

        # 2. Outlier delay (+320 min)
        outlier_row = dict(observations[10])
        outlier_row["actual_arrival"] = outlier_row["scheduled_arrival"] + timedelta(minutes=320)
        outlier_row["delay_min"] = 320.0
        outlier_row["is_outlier"] = True
        observations.append(outlier_row)

        # 3. Negative absurd delay (-180 min - actual before scheduled by hours)
        neg_row = dict(observations[20])
        neg_row["actual_arrival"] = neg_row["scheduled_arrival"] - timedelta(minutes=180)
        neg_row["delay_min"] = -180.0
        neg_row["is_outlier"] = True
        observations.append(neg_row)

        # 4. Unknown stop code
        unknown_stop_row = dict(observations[30])
        unknown_stop_row["stop_code"] = "ST-NONEXISTENT"
        observations.append(unknown_stop_row)

        # 5. Unknown route
        unknown_route_row = dict(observations[40])
        unknown_route_row["route_no"] = "999-UNKNOWN"
        observations.append(unknown_route_row)

    return {
        "routes": routes,
        "stops": stops,
        "route_stops": route_stops,
        "trips": trips,
        "observations": observations,
        "delay_events": delay_events,
    }
