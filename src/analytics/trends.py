"""
BusArrival AI - Transit Analytics and Delay Trend Intelligence
Calculates:
- On-time performance percentages and delay thresholds (On-time <= 2 min, Minor 2-5 min, Major > 5 min)
- Historical delay trends across dimensions: Hour of Day, Day Type, Route, Stop
- 2D Heatmap Matrix (Hour of Day x Day of Week)
- Corridor Route Summaries and Punctuality Metrics
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np


# Standard Transit Punctuality Thresholds (Section 9)
ON_TIME_THRESHOLD_MIN = 2.0      # Arrival within +/- 2.0 min of schedule
MINOR_DELAY_THRESHOLD_MIN = 5.0  # Delay between 2.0 and 5.0 min
# Major Delay: > 5.0 min


DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def compute_punctuality_metrics(delays: List[float]) -> Dict[str, float]:
    """
    Compute distribution metrics, percentiles, and punctuality percentages for a list of delays.
    """
    if not delays:
        return {
            "count": 0,
            "avg_delay": 0.0,
            "median_delay": 0.0,
            "p90_delay": 0.0,
            "on_time_pct": 0.0,
            "minor_delay_pct": 0.0,
            "major_delay_pct": 0.0,
        }

    arr = np.array(delays, dtype=float)
    total = len(arr)
    avg_delay = float(np.mean(arr))
    median_delay = float(np.median(arr))
    p90_delay = float(np.percentile(arr, 90))

    # Punctuality breakdown
    on_time_count = int(np.sum((arr >= -2.0) & (arr <= ON_TIME_THRESHOLD_MIN)))
    minor_delay_count = int(np.sum((arr > ON_TIME_THRESHOLD_MIN) & (arr <= MINOR_DELAY_THRESHOLD_MIN)))
    major_delay_count = int(np.sum(arr > MINOR_DELAY_THRESHOLD_MIN))

    return {
        "count": total,
        "trip_count": total,
        "avg_delay": round(avg_delay, 2),
        "median_delay": round(median_delay, 2),
        "p90_delay": round(p90_delay, 2),
        "on_time_pct": round((on_time_count / total) * 100.0, 1),
        "minor_delay_pct": round((minor_delay_count / total) * 100.0, 1),
        "major_delay_pct": round((major_delay_count / total) * 100.0, 1),
        "major_delays_count": major_delay_count,
        "on_time_count": on_time_count,
    }


def compute_delay_by_hour(observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate arrival delays by scheduled hour of day (0 to 23).
    """
    hourly_groups: Dict[int, List[float]] = {h: [] for h in range(24)}

    for obs in observations:
        dt = obs.get("scheduled_arrival")
        if isinstance(dt, datetime):
            h = dt.hour
        elif isinstance(dt, str):
            try:
                h = datetime.fromisoformat(dt.replace("Z", "+00:00")).hour
            except ValueError:
                continue
        else:
            continue

        try:
            d = float(obs.get("delay_min", 0.0))
            hourly_groups[h].append(d)
        except (ValueError, TypeError):
            pass

    results = []
    for hour in range(24):
        delays = hourly_groups[hour]
        metrics = compute_punctuality_metrics(delays)
        results.append({
            "hour": hour,
            "label": f"{hour:02d}:00",
            **metrics,
        })
    return results


def compute_delay_by_day_type(observations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate arrival delays by day type: weekday vs weekend.
    """
    groups = {"weekday": [], "weekend": []}

    for obs in observations:
        dt = obs.get("scheduled_arrival")
        if isinstance(dt, datetime):
            is_weekend = dt.weekday() >= 5
        elif isinstance(dt, str):
            try:
                is_weekend = datetime.fromisoformat(dt.replace("Z", "+00:00")).weekday() >= 5
            except ValueError:
                continue
        else:
            continue

        key = "weekend" if is_weekend else "weekday"
        try:
            groups[key].append(float(obs.get("delay_min", 0.0)))
        except (ValueError, TypeError):
            pass

    return {
        "weekday": compute_punctuality_metrics(groups["weekday"]),
        "weekend": compute_punctuality_metrics(groups["weekend"]),
    }


def compute_delay_by_route(observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate arrival delays by route.
    """
    route_groups: Dict[str, List[float]] = {}

    for obs in observations:
        r_no = str(obs.get("route_no", "Unknown")).strip()
        try:
            d = float(obs.get("delay_min", 0.0))
            route_groups.setdefault(r_no, []).append(d)
        except (ValueError, TypeError):
            pass

    results = []
    for r_no, delays in sorted(route_groups.items()):
        metrics = compute_punctuality_metrics(delays)
        results.append({
            "route_no": r_no,
            **metrics,
        })
    return results


def compute_delay_by_stop(
    observations: List[Dict[str, Any]],
    route_no: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Aggregate arrival delays by stop, optionally filtered to a single route corridor.
    """
    stop_groups: Dict[str, List[float]] = {}

    for obs in observations:
        if route_no and str(obs.get("route_no", "")).strip() != str(route_no).strip():
            continue
        st = str(obs.get("stop_code", "Unknown")).strip()
        try:
            d = float(obs.get("delay_min", 0.0))
            stop_groups.setdefault(st, []).append(d)
        except (ValueError, TypeError):
            pass

    results = []
    for stop_code, delays in sorted(stop_groups.items()):
        metrics = compute_punctuality_metrics(delays)
        results.append({
            "stop_code": stop_code,
            **metrics,
        })
    return results


def compute_heatmap_matrix(
    observations: List[Dict[str, Any]],
    start_hour: int = 6,
    end_hour: int = 22
) -> List[Dict[str, Any]]:
    """
    Generate 2D matrix of Hour of Day (start_hour to end_hour) x Day of Week (0=Mon to 6=Sun).
    Returns list of cells with average delay and observation density.
    """
    matrix: Dict[tuple, List[float]] = {}
    for h in range(start_hour, end_hour + 1):
        for dow in range(7):
            matrix[(h, dow)] = []

    for obs in observations:
        dt = obs.get("scheduled_arrival")
        if isinstance(dt, datetime):
            h, dow = dt.hour, dt.weekday()
        elif isinstance(dt, str):
            try:
                parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                h, dow = parsed.hour, parsed.weekday()
            except ValueError:
                continue
        else:
            continue

        if (h, dow) in matrix:
            try:
                matrix[(h, dow)].append(float(obs.get("delay_min", 0.0)))
            except (ValueError, TypeError):
                pass

    cells = []
    for (hour, dow), delays in matrix.items():
        avg_delay = round(float(np.mean(delays)), 2) if delays else 0.0
        cells.append({
            "hour": hour,
            "hour_label": f"{hour:02d}:00",
            "day_of_week": dow,
            "day_name": DAY_NAMES[dow],
            "avg_delay_min": avg_delay,
            "sample_count": len(delays),
        })
    return cells


def compute_route_summary(
    routes: List[Dict[str, Any]],
    observations: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Compile executive summary per route joining static route specs with observed delays.
    """
    route_obs_map: Dict[str, List[float]] = {}
    for obs in observations:
        r_no = str(obs.get("route_no", "")).strip()
        try:
            route_obs_map.setdefault(r_no, []).append(float(obs.get("delay_min", 0.0)))
        except (ValueError, TypeError):
            pass

    summaries = []
    for r in routes:
        r_no = r["route_no"]
        delays = route_obs_map.get(r_no, [])
        metrics = compute_punctuality_metrics(delays)

        summaries.append({
            "route_id": str(r.get("_id", r.get("id", ""))),
            "route_no": r_no,
            "route_name": r.get("name", ""),
            "name": r.get("name", ""),
            "origin": r.get("origin", ""),
            "destination": r.get("destination", ""),
            "total_distance_km": r.get("total_distance_km", 0.0),
            "scheduled_headway_min": r.get("scheduled_headway_min", 0),
            "active": r.get("active", True),
            "trip_count": metrics["count"],
            **metrics,
        })
    return summaries
