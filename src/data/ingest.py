"""
BusArrival AI - CSV and GTFS Ingestion Pipeline
Parses, cleans, and validates incoming transit datasets.
Supports standard CSV format and GTFS static format (routes.txt, stops.txt, stop_times.txt).
Supports 'import valid rows only' resolution mode per Section 5.
"""

import io
import csv
from typing import Dict, Any, List, Tuple, Optional, Set
from src.data.validate import validate_routes, validate_stops, validate_observations


def normalize_gtfs_headers(kind: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detects GTFS standard column names and translates them into internal BusArrival AI schema fields.
    Supports routes.txt, stops.txt, trips.txt, stop_times.txt.
    """
    normalized: List[Dict[str, Any]] = []

    for r in rows:
        row = dict(r)

        # GTFS routes.txt mapping
        if kind == "routes":
            if "route_short_name" in row and "route_no" not in row:
                row["route_no"] = row.get("route_short_name") or row.get("route_id", "")
            if "route_long_name" in row and "name" not in row:
                row["name"] = row.get("route_long_name", "")
            if "origin" not in row or not row["origin"]:
                parts = row.get("name", "").split("-")
                row["origin"] = parts[0].strip() if len(parts) > 1 else "Origin Terminal"
                row["destination"] = parts[1].strip() if len(parts) > 1 else "Destination Plaza"
            if "total_distance_km" not in row or not row["total_distance_km"]:
                row["total_distance_km"] = 12.5
            if "scheduled_headway_min" not in row or not row["scheduled_headway_min"]:
                row["scheduled_headway_min"] = 15

        # GTFS stops.txt mapping
        elif kind == "stops":
            if "stop_id" in row and "stop_code" not in row:
                row["stop_code"] = row.get("stop_code") or row.get("stop_id", "")
            if "stop_name" in row and "name" not in row:
                row["name"] = row.get("stop_name", "")
            try:
                lat_val = float(row.get("stop_lat") or row.get("lat") or row.get("latitude") or 0.0)
                lon_val = float(row.get("stop_lon") or row.get("lon") or row.get("longitude") or 0.0)
            except (ValueError, TypeError):
                lat_val, lon_val = 0.0, 0.0
            row["lat"] = lat_val
            row["lon"] = lon_val
            row["latitude"] = lat_val
            row["longitude"] = lon_val

        # GTFS stop_times.txt or observations mapping
        elif kind == "observations":
            if "stop_id" in row and "stop_code" not in row:
                row["stop_code"] = row.get("stop_id", "")
            if "arrival_time" in row and "scheduled_arrival" not in row:
                row["scheduled_arrival"] = row.get("arrival_time", "")
            if "actual_arrival" not in row or not row["actual_arrival"]:
                row["actual_arrival"] = row.get("scheduled_arrival", "")
            if "delay_min" not in row or not row["delay_min"]:
                row["delay_min"] = 0.0

        normalized.append(row)

    return normalized


def parse_csv_content(csv_text: str) -> List[Dict[str, Any]]:
    """Parse CSV or TXT text into a list of sanitized dictionaries."""
    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    rows = []
    for r in reader:
        # Strip string values and normalize whitespace
        cleaned = {k.strip().lower(): v.strip() for k, v in r.items() if k}
        rows.append(cleaned)
    return rows


def process_import(
    kind: str,
    rows: List[Dict[str, Any]],
    valid_route_nos: Optional[Set[str]] = None,
    valid_stop_codes: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """
    Validate imported dataset based on kind ('routes', 'stops', 'observations').
    Applies GTFS auto-normalization then runs Section 5 schema validation rules.
    Returns structured validation report with row-level issue items.
    """
    kind = kind.lower().strip()

    # Step 1: Translate GTFS column headers if present
    normalized_rows = normalize_gtfs_headers(kind, rows)

    # Step 2: Validate against domain rules
    if kind == "routes":
        valid_rows, issues = validate_routes(normalized_rows)
    elif kind == "stops":
        valid_rows, issues = validate_stops(normalized_rows)
    elif kind == "observations":
        valid_rows, issues = validate_observations(
            normalized_rows,
            valid_route_nos=valid_route_nos,
            valid_stop_codes=valid_stop_codes,
        )
    else:
        raise ValueError(f"Unsupported dataset kind '{kind}'. Expected 'routes', 'stops', or 'observations'.")

    return {
        "kind": kind,
        "total_rows": len(rows),
        "valid_count": len(valid_rows),
        "invalid_count": len(rows) - len(valid_rows),
        "issues": issues,
        "valid_rows": valid_rows,
    }
