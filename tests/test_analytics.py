"""
Hand-Calculated Tests for Phase 4: Analytics and Delay Trends.
Validates:
- On-time percentage, minor delay, and major delay formulas vs hand calculations
- Delay trends by hour, day type, route, and stop
- Heatmap matrix generation
- Route summary aggregations
- /analytics router endpoints
"""

import os
from datetime import datetime, timezone
import unittest
from unittest.mock import MagicMock

os.environ["APP_ENV"] = "test"
os.environ["TESTING"] = "true"
os.environ["MONGODB_URI"] = "mongodb://127.0.0.1:27017"
os.environ["JWT_SECRET"] = "super-secret-jwt-key-that-is-at-least-32-chars-long-for-testing"

from src.analytics.trends import (
    compute_punctuality_metrics,
    compute_delay_by_hour,
    compute_delay_by_day_type,
    compute_delay_by_route,
    compute_delay_by_stop,
    compute_heatmap_matrix,
    compute_route_summary,
)
from backend.routers.analytics import get_delay_trends, get_delay_heatmap, get_route_summary
from tests.test_auth import MockDatabase


class TestAnalyticsHandCalculations(unittest.TestCase):
    def test_punctuality_metrics_hand_calculated(self):
        """
        Hand calculation test for punctuality metrics:
        Delays: [-1.0, 0.0, 1.5, 3.0, 7.0]
        - Sum = 10.5 / 5 = 2.1 avg
        - Median = 1.5
        - On-time (-2 to 2 min): [-1.0, 0.0, 1.5] -> 3/5 = 60.0%
        - Minor (2 to 5 min): [3.0] -> 1/5 = 20.0%
        - Major (> 5 min): [7.0] -> 1/5 = 20.0%
        """
        delays = [-1.0, 0.0, 1.5, 3.0, 7.0]
        res = compute_punctuality_metrics(delays)

        self.assertEqual(res["count"], 5)
        self.assertAlmostEqual(res["avg_delay"], 2.1, places=2)
        self.assertAlmostEqual(res["median_delay"], 1.5, places=2)
        self.assertAlmostEqual(res["on_time_pct"], 60.0, places=1)
        self.assertAlmostEqual(res["minor_delay_pct"], 20.0, places=1)
        self.assertAlmostEqual(res["major_delay_pct"], 20.0, places=1)

    def test_delay_by_hour_hand_calculated(self):
        """
        Hand calculation for hourly delay grouping:
        - Obs 1 at 08:15 delay=2.0
        - Obs 2 at 08:45 delay=4.0 -> Hour 8 avg = (2+4)/2 = 3.0 min
        - Obs 3 at 17:20 delay=6.0 -> Hour 17 avg = 6.0 min
        """
        observations = [
            {"scheduled_arrival": datetime(2026, 11, 18, 8, 15, tzinfo=timezone.utc), "delay_min": 2.0},
            {"scheduled_arrival": datetime(2026, 11, 18, 8, 45, tzinfo=timezone.utc), "delay_min": 4.0},
            {"scheduled_arrival": datetime(2026, 11, 18, 17, 20, tzinfo=timezone.utc), "delay_min": 6.0},
        ]
        hourly = compute_delay_by_hour(observations)
        h8 = next(item for item in hourly if item["hour"] == 8)
        h17 = next(item for item in hourly if item["hour"] == 17)
        h12 = next(item for item in hourly if item["hour"] == 12)

        self.assertEqual(h8["count"], 2)
        self.assertAlmostEqual(h8["avg_delay"], 3.0, places=2)
        self.assertEqual(h17["count"], 1)
        self.assertAlmostEqual(h17["avg_delay"], 6.0, places=2)
        self.assertEqual(h12["count"], 0)

    def test_delay_by_day_type_hand_calculated(self):
        """
        Hand calculation for day type:
        - 2026-11-16 (Monday, weekday): delay 2.0
        - 2026-11-17 (Tuesday, weekday): delay 4.0 -> Weekday avg = 3.0
        - 2026-11-21 (Saturday, weekend): delay 1.0 -> Weekend avg = 1.0
        """
        observations = [
            {"scheduled_arrival": datetime(2026, 11, 16, 8, 0, tzinfo=timezone.utc), "delay_min": 2.0},
            {"scheduled_arrival": datetime(2026, 11, 17, 8, 0, tzinfo=timezone.utc), "delay_min": 4.0},
            {"scheduled_arrival": datetime(2026, 11, 21, 10, 0, tzinfo=timezone.utc), "delay_min": 1.0},
        ]
        res = compute_delay_by_day_type(observations)

        self.assertEqual(res["weekday"]["count"], 2)
        self.assertAlmostEqual(res["weekday"]["avg_delay"], 3.0, places=2)
        self.assertEqual(res["weekend"]["count"], 1)
        self.assertAlmostEqual(res["weekend"]["avg_delay"], 1.0, places=2)

    def test_heatmap_matrix_hand_calculated(self):
        """
        Hand calculation for Heatmap matrix:
        2026-11-16 is Monday (dow=0).
        Observation at 08:30 with delay 5.5 -> Cell (hour=8, dow=0) has avg_delay=5.5, count=1.
        """
        observations = [
            {"scheduled_arrival": datetime(2026, 11, 16, 8, 30, tzinfo=timezone.utc), "delay_min": 5.5},
        ]
        cells = compute_heatmap_matrix(observations, start_hour=8, end_hour=10)
        target_cell = next(c for c in cells if c["hour"] == 8 and c["day_of_week"] == 0)

        self.assertEqual(target_cell["day_name"], "Mon")
        self.assertAlmostEqual(target_cell["avg_delay_min"], 5.5, places=2)
        self.assertEqual(target_cell["sample_count"], 1)

    def test_route_summary_hand_calculated(self):
        """
        Hand calculation for Route Summary:
        Route 101: 2 observations [1.0, 3.0] -> avg = 2.0, on_time = 50.0% (1/2)
        Route 204: 2 observations [0.0, -1.0] -> avg = -0.5, on_time = 100.0% (2/2)
        """
        routes = [
            {"route_no": "101", "name": "Express", "total_distance_km": 15.0, "scheduled_headway_min": 15, "active": True},
            {"route_no": "204", "name": "Local", "total_distance_km": 8.0, "scheduled_headway_min": 20, "active": True},
        ]
        observations = [
            {"route_no": "101", "delay_min": 1.0},
            {"route_no": "101", "delay_min": 3.0},
            {"route_no": "204", "delay_min": 0.0},
            {"route_no": "204", "delay_min": -1.0},
        ]
        summaries = compute_route_summary(routes, observations)
        s101 = next(s for s in summaries if s["route_no"] == "101")
        s204 = next(s for s in summaries if s["route_no"] == "204")

        self.assertAlmostEqual(s101["avg_delay"], 2.0, places=2)
        self.assertAlmostEqual(s101["on_time_pct"], 50.0, places=1)
        self.assertAlmostEqual(s204["avg_delay"], -0.5, places=2)
        self.assertAlmostEqual(s204["on_time_pct"], 100.0, places=1)


class TestAnalyticsEndpoints(unittest.TestCase):
    def setUp(self):
        self.mock_db = MockDatabase(name="busarrival_test")
        # Populate mock DB with sample observations
        obs_coll = self.mock_db["observations"]
        obs_coll.insert_one({
            "route_no": "101",
            "stop_code": "ST-001",
            "scheduled_arrival": datetime(2026, 11, 16, 8, 30, tzinfo=timezone.utc),
            "actual_arrival": datetime(2026, 11, 16, 8, 34, tzinfo=timezone.utc),
            "delay_min": 4.0,
        })
        obs_coll.insert_one({
            "route_no": "101",
            "stop_code": "ST-002",
            "scheduled_arrival": datetime(2026, 11, 16, 8, 45, tzinfo=timezone.utc),
            "actual_arrival": datetime(2026, 11, 16, 8, 46, tzinfo=timezone.utc),
            "delay_min": 1.0,
        })
        routes_coll = self.mock_db["routes"]
        routes_coll.insert_one({
            "route_no": "101",
            "name": "Express",
            "origin": "Station A",
            "destination": "Station B",
            "total_distance_km": 12.0,
            "scheduled_headway_min": 15,
            "active": True,
        })

    def test_get_delay_trends_endpoint(self):
        res = get_delay_trends(route_no="101", dimension="all", db=self.mock_db)
        self.assertEqual(res["sample_count"], 2)
        self.assertIn("overall", res)
        self.assertIn("by_hour", res)
        self.assertIn("by_day_type", res)
        self.assertIn("by_stop", res)
        self.assertAlmostEqual(res["overall"]["avg_delay"], 2.5, places=2)

    def test_get_heatmap_endpoint(self):
        res = get_delay_heatmap(route_no="101", start_hour=8, end_hour=10, db=self.mock_db)
        self.assertIn("cells", res)
        self.assertGreater(len(res["cells"]), 0)

    def test_get_route_summary_endpoint(self):
        summaries = get_route_summary(db=self.mock_db)
        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["route_no"], "101")
        self.assertAlmostEqual(summaries[0]["avg_delay"], 2.5, places=2)


if __name__ == "__main__":
    unittest.main()
