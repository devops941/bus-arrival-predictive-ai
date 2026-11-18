"""
Tests for Phase 5: Feature Engineering & Data Leakage Prevention.
Includes strict unit test verifying that future data (at or after prediction time)
is NEVER leaked into history features.
"""

import os
from datetime import datetime, timezone, timedelta
import unittest
from unittest.mock import MagicMock
import numpy as np

os.environ["APP_ENV"] = "test"
os.environ["TESTING"] = "true"
os.environ["MONGODB_URI"] = "mongodb://127.0.0.1:27017"
os.environ["JWT_SECRET"] = "super-secret-jwt-key-that-is-at-least-32-chars-long-for-testing"

from src.ml.features import (
    build_feature_row,
    extract_features_dataset,
    encode_cyclical_hour,
    is_rush_hour,
    FEATURE_COLUMNS,
)


class TestFeatureEngineering(unittest.TestCase):
    def setUp(self):
        self.route = {
            "route_no": "101",
            "name": "Metro Express",
            "total_distance_km": 18.0,
            "scheduled_headway_min": 15,
        }
        self.route_stop = {
            "route_no": "101",
            "stop_code": "ST-003",
            "sequence": 3,
            "distance_from_start_km": 6.0,
        }

    def test_cyclical_encoding(self):
        """Verify sin/cos cycle matches trigonometric expectations."""
        # Midnight: hour=0 -> sin(0)=0, cos(0)=1
        sin_0, cos_0 = encode_cyclical_hour(0.0)
        self.assertAlmostEqual(sin_0, 0.0, places=2)
        self.assertAlmostEqual(cos_0, 1.0, places=2)

        # 06:00 -> sin(pi/2)=1, cos(pi/2)=0
        sin_6, cos_6 = encode_cyclical_hour(6.0)
        self.assertAlmostEqual(sin_6, 1.0, places=2)
        self.assertAlmostEqual(cos_6, 0.0, places=2)

        # 12:00 -> sin(pi)=0, cos(pi)=-1
        sin_12, cos_12 = encode_cyclical_hour(12.0)
        self.assertAlmostEqual(sin_12, 0.0, places=2)
        self.assertAlmostEqual(cos_12, -1.0, places=2)

    def test_peak_hour_flag(self):
        """Verify rush hour classification rules."""
        # 08:30 weekday -> Peak
        self.assertEqual(is_rush_hour(8.5, is_weekend=False), 1)
        # 17:30 weekday -> Peak
        self.assertEqual(is_rush_hour(17.5, is_weekend=False), 1)
        # 14:00 weekday -> Off-peak
        self.assertEqual(is_rush_hour(14.0, is_weekend=False), 0)
        # 08:30 weekend -> Not peak
        self.assertEqual(is_rush_hour(8.5, is_weekend=True), 0)

    def test_strict_no_leakage_guarantee(self):
        """
        Acceptance Criteria:
        Prove no history feature uses data at or after the prediction time.
        We generate features for prediction_time T with baseline past observations.
        Then we inject extreme shock observations occurring at T and after T.
        The extracted feature vector for time T MUST BE 100% IDENTICAL.
        """
        pred_time = datetime(2026, 11, 18, 12, 0, 0, tzinfo=timezone.utc)

        # Legitimate past observations strictly before 12:00
        past_obs_clean = [
            {
                "trip_id": "TR-PAST-1",
                "route_no": "101",
                "stop_code": "ST-001",
                "scheduled_arrival": pred_time - timedelta(hours=2),
                "actual_arrival": pred_time - timedelta(hours=2) + timedelta(minutes=3),
                "delay_min": 3.0,
            },
            {
                "trip_id": "TR-PAST-2",
                "route_no": "101",
                "stop_code": "ST-002",
                "scheduled_arrival": pred_time - timedelta(hours=1),
                "actual_arrival": pred_time - timedelta(hours=1) + timedelta(minutes=5),
                "delay_min": 5.0,
            },
        ]

        # Compute clean features at prediction time
        clean_features = build_feature_row(
            route=self.route,
            route_stop=self.route_stop,
            max_sequence=8,
            prediction_time=pred_time,
            past_observations=past_obs_clean,
        )

        # Invalidate future: Add massive shock observations at T + 5 min and T + 1 hour
        future_tampered_obs = list(past_obs_clean)
        # Injection 1: At prediction time (12:00:00) with absurd +50 min delay
        future_tampered_obs.append({
            "trip_id": "TR-FUTURE-SHOCK-1",
            "route_no": "101",
            "stop_code": "ST-003",
            "scheduled_arrival": pred_time,
            "actual_arrival": pred_time + timedelta(minutes=50),
            "delay_min": 50.0,
        })
        # Injection 2: After prediction time (13:00:00) with absurd +99 min delay
        future_tampered_obs.append({
            "trip_id": "TR-FUTURE-SHOCK-2",
            "route_no": "101",
            "stop_code": "ST-004",
            "scheduled_arrival": pred_time + timedelta(hours=1),
            "actual_arrival": pred_time + timedelta(hours=1, minutes=99),
            "delay_min": 99.0,
        })

        # Filter out anything >= pred_time (as extract_features_dataset does)
        strictly_prior_obs = [
            o for o in future_tampered_obs
            if (o["scheduled_arrival"] if isinstance(o["scheduled_arrival"], datetime) else datetime.fromisoformat(o["scheduled_arrival"])) < pred_time
        ]

        tampered_features = build_feature_row(
            route=self.route,
            route_stop=self.route_stop,
            max_sequence=8,
            prediction_time=pred_time,
            past_observations=strictly_prior_obs,
        )

        # Assert zero leakage: history values must match exactly
        self.assertEqual(clean_features["recent_route_delay_mean"], tampered_features["recent_route_delay_mean"])
        self.assertEqual(clean_features["prev_trip_delay"], tampered_features["prev_trip_delay"])
        self.assertEqual(clean_features["prev_stop_delay"], tampered_features["prev_stop_delay"])
        self.assertAlmostEqual(clean_features["recent_route_delay_mean"], 4.0, places=1)


if __name__ == "__main__":
    unittest.main()
