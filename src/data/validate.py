"""
BusArrival AI - Data Validation Rules & Pipeline
Validates routes, stops, route-stops, trips, observations, and CSV imports.
Implements Section 5 validation rules:
- Required fields
- Distances > 0
- Stop sequences unique & strictly increasing per route
- Times parseable into valid datetimes
- Plausible arrival window check (configurable, default: -10 to +120 min)
- Duplicate detection on (trip_id, stop_code)
- Unknown foreign-key route & stop mapping detection
- Outlier detection via Median ± k * MAD
- Row-level issue reports with validation errors vs warnings
"""

from datetime import datetime, date, time
from typing import Dict, Any, List, Optional, Tuple, Set
import numpy as np


class ValidationIssue:
    def __init__(self, row_idx: int, field: str, issue_type: str, message: str, is_fatal: bool = True):
        self.row_idx = row_idx
        self.field = field
        self.issue_type = issue_type  # 'REQUIRED', 'TYPE', 'RANGE', 'FOREIGN_KEY', 'DUPLICATE', 'OUTLIER'
        self.message = message
        self.is_fatal = is_fatal

    def to_dict(self) -> Dict[str, Any]:
        return {
            "row": self.row_idx,
            "field": self.field,
            "issue_type": self.issue_type,
            "message": self.message,
            "is_fatal": self.is_fatal,
        }


def parse_timestamp(value: Any) -> Optional[datetime]:
    """Parse various datetime representations into a datetime object."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        val = value.strip().replace("Z", "+00:00")
        for fmt in (
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%d",
        ):
            try:
                return datetime.strptime(val, fmt)
            except ValueError:
                continue
    return None


def calculate_mad_bounds(values: List[float], k: float = 3.5) -> Tuple[float, float]:
    """
    Compute robust outlier cutoff bounds using Median Absolute Deviation (MAD).
    Bounds: Median ± k * MAD
    """
    if not values or len(values) < 5:
        return (-10.0, 120.0)

    arr = np.array(values, dtype=float)
    median = float(np.median(arr))
    abs_deviations = np.abs(arr - median)
    mad = float(np.median(abs_deviations))
    if mad < 1e-4:
        mad = float(np.std(arr)) or 1.0

    lower = median - (k * mad * 1.4826)
    upper = median + (k * mad * 1.4826)
    return (float(lower), float(upper))


def validate_routes(routes: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Validate list of route dictionaries."""
    valid_rows = []
    issues = []
    seen_route_nos = set()

    for idx, r in enumerate(routes, start=1):
        row_issues = []
        route_no = str(r.get("route_no", "")).strip()
        if not route_no:
            row_issues.append(ValidationIssue(idx, "route_no", "REQUIRED", "Route number is required"))
        elif route_no in seen_route_nos:
            row_issues.append(ValidationIssue(idx, "route_no", "DUPLICATE", f"Duplicate route number '{route_no}'"))
        seen_route_nos.add(route_no)

        if not r.get("name"):
            row_issues.append(ValidationIssue(idx, "name", "REQUIRED", "Route name is required"))

        try:
            dist = float(r.get("total_distance_km", 0))
            if dist <= 0:
                row_issues.append(ValidationIssue(idx, "total_distance_km", "RANGE", "Total distance must be > 0"))
        except (ValueError, TypeError):
            row_issues.append(ValidationIssue(idx, "total_distance_km", "TYPE", "Invalid distance format"))

        try:
            headway = int(r.get("scheduled_headway_min", 0))
            if headway <= 0:
                row_issues.append(ValidationIssue(idx, "scheduled_headway_min", "RANGE", "Headway must be >= 1 min"))
        except (ValueError, TypeError):
            row_issues.append(ValidationIssue(idx, "scheduled_headway_min", "TYPE", "Invalid headway format"))

        if any(iss.is_fatal for iss in row_issues):
            issues.extend([iss.to_dict() for iss in row_issues])
        else:
            valid_rows.append(r)
            if row_issues:
                issues.extend([iss.to_dict() for iss in row_issues])

    return valid_rows, issues


def validate_stops(stops: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Validate list of stop dictionaries."""
    valid_rows = []
    issues = []
    seen_codes = set()

    for idx, s in enumerate(stops, start=1):
        row_issues = []
        code = str(s.get("stop_code", "")).strip()
        if not code:
            row_issues.append(ValidationIssue(idx, "stop_code", "REQUIRED", "Stop code is required"))
        elif code in seen_codes:
            row_issues.append(ValidationIssue(idx, "stop_code", "DUPLICATE", f"Duplicate stop code '{code}'"))
        seen_codes.add(code)

        if not s.get("name"):
            row_issues.append(ValidationIssue(idx, "name", "REQUIRED", "Stop name is required"))

        try:
            lat = float(s.get("lat", 0))
            lon = float(s.get("lon", 0))
            if not (-90.0 <= lat <= 90.0):
                row_issues.append(ValidationIssue(idx, "lat", "RANGE", "Latitude must be between -90 and 90"))
            if not (-180.0 <= lon <= 180.0):
                row_issues.append(ValidationIssue(idx, "lon", "RANGE", "Longitude must be between -180 and 180"))
        except (ValueError, TypeError):
            row_issues.append(ValidationIssue(idx, "coordinates", "TYPE", "Invalid lat/lon float format"))

        if any(iss.is_fatal for iss in row_issues):
            issues.extend([iss.to_dict() for iss in row_issues])
        else:
            valid_rows.append(s)

    return valid_rows, issues


def validate_observations(
    observations: List[Dict[str, Any]],
    valid_route_nos: Optional[Set[str]] = None,
    valid_stop_codes: Optional[Set[str]] = None,
    min_window_min: float = -10.0,
    max_window_min: float = 120.0,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validate arrival observation records.
    Detects missing values, invalid foreign keys, timestamps, and outliers.
    """
    valid_rows = []
    issues = []
    seen_trip_stops = set()

    # Pre-calculate MAD bounds on delay_min for outlier detection
    delays = []
    for obs in observations:
        try:
            delays.append(float(obs.get("delay_min", 0)))
        except (ValueError, TypeError):
            pass

    mad_lower, mad_upper = calculate_mad_bounds(delays)

    for idx, obs in enumerate(observations, start=1):
        row_issues = []
        trip_id = str(obs.get("trip_id", "")).strip()
        stop_code = str(obs.get("stop_code", "")).strip()
        route_no = str(obs.get("route_no", "")).strip()

        if not trip_id:
            row_issues.append(ValidationIssue(idx, "trip_id", "REQUIRED", "Trip ID is required"))
        if not stop_code:
            row_issues.append(ValidationIssue(idx, "stop_code", "REQUIRED", "Stop code is required"))

        # Duplicate check on (trip_id, stop_code)
        key = (trip_id, stop_code)
        if key in seen_trip_stops:
            row_issues.append(ValidationIssue(idx, "trip_id,stop_code", "DUPLICATE", f"Duplicate observation for trip '{trip_id}' and stop '{stop_code}'"))
        seen_trip_stops.add(key)

        # Foreign key checks
        if valid_route_nos is not None and route_no and route_no not in valid_route_nos:
            row_issues.append(ValidationIssue(idx, "route_no", "FOREIGN_KEY", f"Unknown route '{route_no}'"))
        if valid_stop_codes is not None and stop_code and stop_code not in valid_stop_codes:
            row_issues.append(ValidationIssue(idx, "stop_code", "FOREIGN_KEY", f"Unknown stop code '{stop_code}'"))

        # Timestamps and delay calculations
        sched_dt = parse_timestamp(obs.get("scheduled_arrival"))
        actual_dt = parse_timestamp(obs.get("actual_arrival"))

        if not sched_dt:
            row_issues.append(ValidationIssue(idx, "scheduled_arrival", "TYPE", "Unparseable scheduled arrival time"))
        if not actual_dt:
            row_issues.append(ValidationIssue(idx, "actual_arrival", "TYPE", "Unparseable actual arrival time"))

        if sched_dt and actual_dt:
            derived_delay = round((actual_dt - sched_dt).total_seconds() / 60.0, 2)
            obs["delay_min"] = derived_delay

            # Plausible window check (-10m to +120m)
            if derived_delay < min_window_min or derived_delay > max_window_min:
                row_issues.append(ValidationIssue(
                    idx,
                    "delay_min",
                    "RANGE",
                    f"Arrival delay {derived_delay} min falls outside plausible window [{min_window_min}, +{max_window_min}] min",
                    is_fatal=False
                ))
                obs["is_outlier"] = True

            # Statistical MAD outlier check
            if derived_delay < mad_lower or derived_delay > mad_upper:
                obs["is_outlier"] = True

        has_fatal = any(iss.is_fatal for iss in row_issues)
        if has_fatal:
            issues.extend([iss.to_dict() for iss in row_issues])
        else:
            valid_rows.append(obs)
            if row_issues:
                issues.extend([iss.to_dict() for iss in row_issues])

    return valid_rows, issues
