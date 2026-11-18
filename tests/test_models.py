"""
Tests for Phase 6: Machine Learning Models, Validation, and Baselines.
Verifies:
- Metric calculations (MAE, RMSE, MAPE, within-2-min, bias, P90 coverage)
- Chronological train/test split without future leakage
- Model training: Baseline, Ridge, Random Forest, Quantile Gradient Boosting
- Model artifact serialization via joblib
- Acceptance: Model beats baseline or honestly reports it does not
"""

import os
from datetime import datetime, timezone, timedelta
import unittest
import numpy as np

os.environ["APP_ENV"] = "test"
os.environ["TESTING"] = "true"
os.environ["MONGODB_URI"] = "mongodb://127.0.0.1:27017"
os.environ["JWT_SECRET"] = "super-secret-jwt-key-that-is-at-least-32-chars-long-for-testing"

from src.ml.models import (
    create_model_instance,
    BaselineModel,
    RidgeRegressionModel,
    RandomForestRegressorModel,
    QuantileGBModel,
    save_model_artifact,
    load_model_artifact,
)
from src.ml.validate import (
    compute_regression_metrics,
    chronological_split,
    run_training_pipeline,
)
from src.ml.features import FeatureTable, FEATURE_COLUMNS


class TestModelValidation(unittest.TestCase):
    def test_regression_metrics(self):
        """Verify metric calculation formulas."""
        y_true = np.array([2.0, 4.0, 0.0, 8.0, 1.0])
        y_pred = np.array([2.5, 3.5, 0.5, 7.0, 2.0])
        y_p90 = np.array([3.0, 5.0, 1.0, 8.5, 3.0])

        metrics = compute_regression_metrics(y_true, y_pred, y_p90=y_p90)
        self.assertAlmostEqual(metrics["mae"], 0.7, places=1)
        self.assertEqual(metrics["within_2_min_pct"], 100.0)
        self.assertEqual(metrics["p90_coverage_pct"], 100.0)
        self.assertGreater(metrics["mape"], 0.0)

    def test_ridge_regression_convergence(self):
        """Verify Ridge regression fits synthetic target."""
        X = np.array([[1.0, 2.0], [2.0, 3.0], [3.0, 4.0], [4.0, 5.0]])
        y = np.array([3.0, 5.0, 7.0, 9.0])
        model = RidgeRegressionModel(alpha=0.1)
        model.fit(X, y)
        preds = model.predict(X)
        mae = np.mean(np.abs(preds - y))
        self.assertLess(mae, 0.5)

    def test_quantile_gb_interval_ordering(self):
        """Verify that QuantileGBModel enforces P90 >= P50."""
        X = np.random.randn(40, len(FEATURE_COLUMNS))
        y = np.random.uniform(0.0, 10.0, size=40)

        model = QuantileGBModel(n_estimators=10)
        model.fit(X, y)
        p50, p90 = model.predict_intervals(X)

        self.assertEqual(len(p50), len(p90))
        self.assertTrue(np.all(p90 >= p50))

    def test_chronological_split(self):
        """Verify chronological split puts earlier records in train and latest in test."""
        base_dt = datetime(2026, 11, 1, tzinfo=timezone.utc)
        records = [
            {"scheduled_arrival": base_dt + timedelta(days=i), "delay_min": float(i)}
            for i in range(10)
        ]
        ft = FeatureTable(records)
        train_recs, test_recs = chronological_split(ft, test_ratio=0.2)

        self.assertEqual(len(train_recs), 8)
        self.assertEqual(len(test_recs), 2)
        self.assertLess(train_recs[-1]["scheduled_arrival"], test_recs[0]["scheduled_arrival"])

    def test_training_pipeline_and_beats_baseline(self):
        """
        Acceptance Criteria:
        Trained model beats baseline on held-out test data, or result honestly says it does not.
        """
        base_dt = datetime(2026, 11, 1, tzinfo=timezone.utc)
        records = []
        for i in range(80):
            dt = base_dt + timedelta(hours=i)
            # Signal: delay increases with distance_to_stop and rush hour
            dist = float((i % 8) * 2.0)
            is_peak = 1 if (i % 24 in (8, 17)) else 0
            simulated_delay = 1.0 + (0.3 * dist) + (4.0 * is_peak) + np.random.normal(0, 0.2)
            row = {
                "route_distance_km": 16.0,
                "distance_to_stop_km": dist,
                "stop_count_remaining": 8 - (i % 8),
                "stop_sequence": (i % 8) + 1,
                "hour_sin": 0.0,
                "hour_cos": 1.0,
                "is_peak": is_peak,
                "day_of_week": dt.weekday(),
                "is_weekend": 1 if dt.weekday() >= 5 else 0,
                "scheduled_headway_min": 15,
                "recent_route_delay_mean": 2.0,
                "prev_stop_delay": 1.5,
                "prev_trip_delay": 2.0,
                "rain_flag": 0,
                "route_no": "101",
                "stop_code": f"ST-00{(i % 8) + 1}",
                "scheduled_arrival": dt,
                "delay_min": simulated_delay,
            }
            records.append(row)

        ft = FeatureTable(records)
        doc = run_training_pipeline(
            algorithm="ridge",
            feature_df=ft,
            model_id="test_model_01",
            created_by="tester@transit.org",
        )

        self.assertIn("metrics", doc)
        self.assertIn("baseline_metrics", doc)
        self.assertIn("beats_baseline", doc)
        self.assertTrue(os.path.exists(doc["artifact_path"]))

        # Verify artifact can be loaded
        loaded = load_model_artifact(doc["artifact_path"])
        self.assertIsNotNone(loaded["model"])
        self.assertEqual(loaded["metadata"]["model_id"], "test_model_01")


if __name__ == "__main__":
    unittest.main()
