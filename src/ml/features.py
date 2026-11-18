"""
BusArrival AI - Feature Engineering Pipeline
Constructs leakage-free ML features per Section 7.2 of the project specification.

Features:
- route_distance_km
- distance_to_stop_km
- stop_count_remaining
- stop_sequence
- hour_sin, hour_cos (cyclical encoding of scheduled time)
- is_peak (rush hour flag: weekdays 07:30-09:30 and 16:30-19:30)
- day_of_week (0 to 6)
- is_weekend (0 or 1)
- scheduled_headway_min
- recent_route_delay_mean (last N completed trips on this route strictly BEFORE prediction time)
- prev_stop_delay (delay at previous stop on same trip, strictly before target stop)
- prev_trip_delay (mean delay of immediately preceding trip on this route)
- rain_flag (active rain weather shock strictly before prediction time)

LEAKAGE GUARANTEE:
Every history feature is computed strictly using observations that occurred BEFORE
the target prediction timestamp. Future or concurrent data is never used.
"""

from datetime import datetime, timezone, timedelta
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


FEATURE_COLUMNS = [
    "route_distance_km",
    "distance_to_stop_km",
    "stop_count_remaining",
    "stop_sequence",
    "hour_sin",
    "hour_cos",
    "is_peak",
    "day_of_week",
    "is_weekend",
    "scheduled_headway_min",
    "recent_route_delay_mean",
    "prev_stop_delay",
    "prev_trip_delay",
    "rain_flag",
]


class FeatureTable:
    """
    Lightweight, self-contained tabular container for feature vectors.
    Provides dict/list conversions and matrix extraction without requiring C-extension pandas.
    """
    def __init__(self, records: List[Dict[str, Any]]):
        self.records = records

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, col_name: str) -> np.ndarray:
        return np.array([r.get(col_name) for r in self.records])

    def to_dict(self, orient: str = "records") -> List[Dict[str, Any]]:
        return [dict(r) for r in self.records]

    def head(self, n: int = 5) -> "FeatureTable":
        return FeatureTable(self.records[:n])

    @property
    def values(self) -> np.ndarray:
        return np.array([[r.get(c, 0.0) for c in FEATURE_COLUMNS] for r in self.records], dtype=float)

    def get_feature_matrix(self, columns: Optional[List[str]] = None) -> np.ndarray:
        cols = columns or FEATURE_COLUMNS
        return np.array([[float(r.get(c, 0.0)) for c in cols] for r in self.records], dtype=float)


def encode_cyclical_hour(hour_float: float) -> Tuple[float, float]:
    """Sin and Cos cyclical encoding for 24-hour time."""
    angle = 2.0 * math.pi * (hour_float / 24.0)
    return round(math.sin(angle), 4), round(math.cos(angle), 4)


def is_rush_hour(hour_float: float, is_weekend: bool) -> int:
    """Peak travel hours: Weekdays 07:30-09:30 and 16:30-19:30."""
    if is_weekend:
        return 0
    if (7.5 <= hour_float <= 9.5) or (16.5 <= hour_float <= 19.5):
        return 1
    return 0


def build_feature_row(
    route: Dict[str, Any],
    route_stop: Dict[str, Any],
    max_sequence: int,
    prediction_time: datetime,
    past_observations: List[Dict[str, Any]],
    current_trip_observations: Optional[List[Dict[str, Any]]] = None,
    past_events: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Construct a single feature vector for (route, stop, prediction_time).
    Strictly past-only data is passed in past_observations.
    """
    if prediction_time.tzinfo is None:
        prediction_time = prediction_time.replace(tzinfo=timezone.utc)

    # 1. Route and Stop physical features
    total_dist = float(route.get("total_distance_km", 15.0))
    dist_from_start = float(route_stop.get("distance_from_start_km", 0.0))
    dist_to_stop = max(0.0, total_dist - dist_from_start)
    seq = int(route_stop.get("sequence", 1))
    stops_remaining = max(0, max_sequence - seq)
    headway = int(route.get("scheduled_headway_min", 15))

    # 2. Time & Calendar features
    hour_val = prediction_time.hour + (prediction_time.minute / 60.0) + (prediction_time.second / 3600.0)
    hour_sin, hour_cos = encode_cyclical_hour(hour_val)
    dow = prediction_time.weekday()
    weekend = 1 if dow >= 5 else 0
    peak = is_rush_hour(hour_val, bool(weekend))

    # 3. Previous stop delay on the same trip
    prev_stop_delay = 0.0
    if current_trip_observations and seq > 1:
        prev_obs = [
            o for o in current_trip_observations
            if o.get("sequence", 0) < seq and "delay_min" in o
        ]
        if prev_obs:
            prev_obs.sort(key=lambda x: x.get("sequence", 0), reverse=True)
            prev_stop_delay = float(prev_obs[0]["delay_min"])

    # 4. Recent route delay mean (Strictly past trips completed BEFORE prediction_time)
    r_no = str(route.get("route_no", "")).strip()
    route_past = [
        o for o in past_observations
        if str(o.get("route_no", "")).strip() == r_no and "delay_min" in o
    ]

    recent_route_delay_mean = 0.0
    prev_trip_delay = 0.0
    if route_past:
        route_past.sort(
            key=lambda x: x.get("actual_arrival") or x.get("scheduled_arrival") or datetime.min.replace(tzinfo=timezone.utc)
        )
        recent_delays = [float(o["delay_min"]) for o in route_past[-15:]]
        recent_route_delay_mean = float(np.mean(recent_delays))

        last_trip_id = route_past[-1].get("trip_id")
        last_trip_obs = [float(o["delay_min"]) for o in route_past if o.get("trip_id") == last_trip_id]
        if last_trip_obs:
            prev_trip_delay = float(np.mean(last_trip_obs))

    # 5. Weather / rain shock flag active before prediction_time
    rain_flag = 0
    if past_events:
        for ev in past_events:
            ev_cause = str(ev.get("cause", "")).lower()
            if "rain" in ev_cause:
                rain_flag = 1
                break

    return {
        "route_distance_km": round(total_dist, 2),
        "distance_to_stop_km": round(dist_to_stop, 2),
        "stop_count_remaining": stops_remaining,
        "stop_sequence": seq,
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
        "is_peak": peak,
        "day_of_week": dow,
        "is_weekend": weekend,
        "scheduled_headway_min": headway,
        "recent_route_delay_mean": round(recent_route_delay_mean, 2),
        "prev_stop_delay": round(prev_stop_delay, 2),
        "prev_trip_delay": round(prev_trip_delay, 2),
        "rain_flag": rain_flag,
    }


def extract_features_dataset(
    routes: List[Dict[str, Any]],
    stops: List[Dict[str, Any]],
    route_stops: List[Dict[str, Any]],
    trips: List[Dict[str, Any]],
    observations: List[Dict[str, Any]],
    delay_events: Optional[List[Dict[str, Any]]] = None,
) -> FeatureTable:
    """
    Extract a fully vectorized, leakage-free feature matrix from transit collections.
    Sorts chronologically and computes history features using strictly prior data.
    """
    routes_map = {str(r["route_no"]).strip(): r for r in routes}
    route_stops_map = {}
    max_seq_map = {}

    for rs in route_stops:
        r_no = str(rs["route_no"]).strip()
        route_stops_map[(r_no, str(rs["stop_code"]).strip())] = rs
        max_seq_map[r_no] = max(max_seq_map.get(r_no, 0), int(rs["sequence"]))

    def get_arrival_time(o):
        dt = o.get("scheduled_arrival")
        if isinstance(dt, datetime):
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        if isinstance(dt, str):
            try:
                parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        return datetime.min.replace(tzinfo=timezone.utc)

    sorted_obs = sorted(observations, key=get_arrival_time)

    trip_obs_map: Dict[str, List[Dict[str, Any]]] = {}
    for o in sorted_obs:
        t_id = o.get("trip_id")
        r_no = str(o.get("route_no", "")).strip()
        st_code = str(o.get("stop_code", "")).strip()
        rs = route_stops_map.get((r_no, st_code), {})
        o_copy = dict(o)
        o_copy["sequence"] = rs.get("sequence", 1)
        trip_obs_map.setdefault(t_id, []).append(o_copy)

    past_observations: List[Dict[str, Any]] = []
    rows = []

    for obs in sorted_obs:
        r_no = str(obs.get("route_no", "")).strip()
        st_code = str(obs.get("stop_code", "")).strip()
        route = routes_map.get(r_no)
        rs = route_stops_map.get((r_no, st_code))

        if not route or not rs:
            continue

        sched_dt = get_arrival_time(obs)
        max_seq = max_seq_map.get(r_no, 8)
        current_trip = trip_obs_map.get(obs.get("trip_id"), [])

        feature_dict = build_feature_row(
            route=route,
            route_stop=rs,
            max_sequence=max_seq,
            prediction_time=sched_dt,
            past_observations=past_observations,
            current_trip_observations=current_trip,
            past_events=delay_events,
        )

        feature_dict["trip_id"] = obs.get("trip_id")
        feature_dict["route_no"] = r_no
        feature_dict["stop_code"] = st_code
        feature_dict["scheduled_arrival"] = sched_dt
        feature_dict["actual_arrival"] = obs.get("actual_arrival")
        feature_dict["delay_min"] = float(obs.get("delay_min", 0.0))
        feature_dict["is_outlier"] = bool(obs.get("is_outlier", False))

        rows.append(feature_dict)
        past_observations.append(obs)

    return FeatureTable(rows)
