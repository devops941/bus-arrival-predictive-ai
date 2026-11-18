"""
Tests for GTFS static import parsing and auto-header normalization (Phase 13).
"""

import unittest
from pathlib import Path
from src.data.ingest import parse_csv_content, process_import, normalize_gtfs_headers


class TestGTFSStaticImport(unittest.TestCase):
    def test_gtfs_routes_normalization(self):
        gtfs_routes_csv = (
            "route_id,agency_id,route_short_name,route_long_name,route_type,route_color\n"
            "R-201,AGY,201,North Station - Tech Park Express,3,1D4ED8\n"
        )
        rows = parse_csv_content(gtfs_routes_csv)
        report = process_import("routes", rows)
        self.assertEqual(report["total_rows"], 1)
        self.assertEqual(report["valid_count"], 1)
        valid = report["valid_rows"][0]
        self.assertEqual(valid["route_no"], "201")
        self.assertEqual(valid["name"], "North Station - Tech Park Express")
        self.assertEqual(valid["origin"], "North Station")
        self.assertEqual(valid["destination"], "Tech Park Express")

    def test_gtfs_stops_normalization(self):
        gtfs_stops_csv = (
            "stop_id,stop_code,stop_name,stop_lat,stop_lon,location_type\n"
            "ST-101,ST-101,North Station Platform A,28.6200,77.2100,0\n"
            "ST-102,ST-102,Tech Park Central Terminal,28.6350,77.2250,0\n"
        )
        rows = parse_csv_content(gtfs_stops_csv)
        report = process_import("stops", rows)
        self.assertEqual(report["total_rows"], 2)
        self.assertEqual(report["valid_count"], 2)
        self.assertEqual(len(report["issues"]), 0)
        self.assertAlmostEqual(report["valid_rows"][0]["latitude"], 28.6200)

    def test_gtfs_observations_normalization(self):
        gtfs_stop_times_csv = (
            "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
            "TR-201-01,2026-11-18T08:00:00Z,2026-11-18T08:00:30Z,ST-101,1\n"
        )
        rows = parse_csv_content(gtfs_stop_times_csv)
        report = process_import("observations", rows)
        self.assertEqual(report["total_rows"], 1)
        self.assertEqual(report["valid_count"], 1)
        valid = report["valid_rows"][0]
        self.assertEqual(valid["trip_id"], "TR-201-01")
        self.assertEqual(valid["stop_code"], "ST-101")


if __name__ == "__main__":
    unittest.main()
