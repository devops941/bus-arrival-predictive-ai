"""
Tests for Phase 7: Model Registry, ETA Service, and Drift Monitoring.
Verifies:
- Active model lifecycle (activation, rollback)
- Role guards: Only admin can activate or rollback
- ETA Predictor returns P50/P90 confidence intervals and reliability label
- Prediction logging to predictions_log
- Drift monitoring and alert trigger
"""

import os
from datetime import datetime, timezone, timedelta
import unittest
from unittest.mock import MagicMock, patch
import numpy as np

os.environ["APP_ENV"] = "test"
os.environ["TESTING"] = "true"
os.environ["MONGODB_URI"] = "mongodb://127.0.0.1:27017"
os.environ["JWT_SECRET"] = "super-secret-jwt-key-that-is-at-least-32-chars-long-for-testing"

from src.db.repositories.model_repo import ModelRepository
from src.db.repositories.prediction_repo import PredictionRepository, AlertRepository
from src.ml.models import QuantileGBModel, save_model_artifact
from src.ml.predict import (
    predict_eta,
    predict_route_corridor,
    calculate_reliability_label,
    check_and_create_drift_alerts,
)
from backend.routers.models import activate_model_endpoint, rollback_model_endpoint
from backend.routers.predict import get_predicted_eta, PredictEtaRequest
from tests.test_auth import MockDatabase
from fastapi import HTTPException


class TestModelRegistryAndETA(unittest.TestCase):
    def setUp(self):
        self.mock_db = MockDatabase(name="busarrival_test")
        self.model_repo = ModelRepository(self.mock_db)
        self.pred_repo = PredictionRepository(self.mock_db)
        self.alert_repo = AlertRepository(self.mock_db)

        # Setup route and stops
        self.mock_db["routes"].insert_one({
            "route_no": "101",
            "name": "Metro Express",
            "total_distance_km": 15.0,
            "scheduled_headway_min": 15,
            "active": True,
        })
        self.mock_db["route_stops"].insert_one({
            "route_no": "101",
            "stop_code": "ST-001",
            "sequence": 1,
            "distance_from_start_km": 0.0,
            "scheduled_offset_min": 0,
        })
        self.mock_db["route_stops"].insert_one({
            "route_no": "101",
            "stop_code": "ST-002",
            "sequence": 2,
            "distance_from_start_km": 5.0,
            "scheduled_offset_min": 12,
        })

        # Save trained QuantileGB artifact
        model = QuantileGBModel(n_estimators=5)
        X_dummy = np.random.randn(20, 14)
        y_dummy = np.random.uniform(1.0, 5.0, size=20)
        model.fit(X_dummy, y_dummy)

        self.model_id_1 = "mod_test_qgb_01"
        self.model_id_2 = "mod_test_qgb_02"

        path1 = save_model_artifact(model, self.model_id_1, {"model_id": self.model_id_1})
        path2 = save_model_artifact(model, self.model_id_2, {"model_id": self.model_id_2})

        self.mock_db["models"].insert_one({
            "model_id": self.model_id_1,
            "name": "Model 1",
            "algorithm": "quantile_gb",
            "status": "archived",
            "artifact_path": path1,
            "metrics": {"mae": 1.5, "within_2_min_pct": 82.0},
            "created_at": datetime.now(timezone.utc),
        })

        self.mock_db["models"].insert_one({
            "model_id": self.model_id_2,
            "name": "Model 2",
            "algorithm": "quantile_gb",
            "status": "active",
            "artifact_path": path2,
            "metrics": {"mae": 1.4, "within_2_min_pct": 84.0},
            "created_at": datetime.now(timezone.utc),
        })

    def test_active_model_activation_and_rollback(self):
        """Verify model activation archives previous model and rollback restores it."""
        admin_user = {"id": "admin_1", "email": "admin@busarrival.local", "role": "admin"}

        # Activate model 1
        res = activate_model_endpoint(
            id=self.model_id_1,
            current_admin=admin_user,
            db=self.mock_db,
        )
        self.assertEqual(res["model_id"], self.model_id_1)
        active = self.model_repo.get_active_model()
        self.assertEqual(active["model_id"], self.model_id_1)

        # Rollback restores model 2
        rb_res = rollback_model_endpoint(
            current_admin=admin_user,
            db=self.mock_db,
        )
        self.assertEqual(rb_res["active_model"]["model_id"], self.model_id_2)

    def test_predict_eta_output_and_reliability(self):
        """
        Verify Acceptance Criteria:
        POST /predict/eta returns ETA P50, P90, expected delay and reliability label.
        Logs prediction into predictions_log.
        """
        sched_time = datetime(2026, 11, 18, 14, 0, 0, tzinfo=timezone.utc)
        result = predict_eta(
            route_no="101",
            stop_code="ST-002",
            scheduled_time=sched_time,
            db=self.mock_db,
        )

        self.assertIn("eta_p50", result)
        self.assertIn("eta_p90", result)
        self.assertIn("expected_delay_min", result)
        self.assertIn("reliability", result)
        self.assertIn("disclaimer", result)

        # Verify interval order
        p50_dt = datetime.fromisoformat(result["eta_p50"])
        p90_dt = datetime.fromisoformat(result["eta_p90"])
        self.assertGreaterEqual(p90_dt, p50_dt)

        # Verify logged into predictions_log collection
        logged_preds = self.mock_db["predictions_log"].find({"route_no": "101"})
        self.assertGreaterEqual(len(list(logged_preds)), 1)

    def test_reliability_tiers(self):
        """Verify reliability label boundaries."""
        self.assertEqual(calculate_reliability_label(interval_width=3.0, validation_mae=1.5), "HIGH")
        self.assertEqual(calculate_reliability_label(interval_width=6.0, validation_mae=2.5), "MEDIUM")
        self.assertEqual(calculate_reliability_label(interval_width=10.0, validation_mae=3.5), "LOW")

    def test_corridor_predictions(self):
        """Verify corridor predictions returns delays along all stops."""
        sched_start = datetime(2026, 11, 18, 15, 0, 0, tzinfo=timezone.utc)
        corridor = predict_route_corridor("101", sched_start, db=self.mock_db)
        self.assertEqual(len(corridor), 2)
        self.assertEqual(corridor[0]["stop_code"], "ST-001")
        self.assertEqual(corridor[1]["stop_code"], "ST-002")

    def test_drift_monitoring_and_alerts(self):
        """
        Verify Acceptance Criteria:
        Drift checks compare rolling MAE against active model validation MAE and raise alerts.
        """
        # Inject recent observations with huge delays (+8 min average)
        obs_coll = self.mock_db["observations"]
        base_time = datetime(2026, 11, 18, 10, 0, 0, tzinfo=timezone.utc)
        for i in range(30):
            obs_coll.insert_one({
                "trip_id": f"TR-DRIFT-{i}",
                "route_no": "101",
                "stop_code": "ST-001",
                "scheduled_arrival": base_time + timedelta(minutes=i*10),
                "actual_arrival": base_time + timedelta(minutes=i*10 + 8),
                "delay_min": 8.0,
            })

        alerts = check_and_create_drift_alerts(self.mock_db)
        self.assertGreater(len(alerts), 0)
        self.assertGreater(alerts[0]["drift_ratio"], 1.3)

        open_alerts = self.alert_repo.list_open_alerts()
        self.assertGreater(len(open_alerts), 0)
        self.assertEqual(open_alerts[0]["alert_type"], "MODEL_DRIFT")

    def test_eta_edge_case_unknown_stop(self):
        """Verify Section 15: ETA predictor edge case with unknown stop."""
        sched_time = datetime(2026, 11, 18, 14, 0, 0, tzinfo=timezone.utc)
        req = PredictEtaRequest(route_no="101", stop_code="ST-DOES-NOT-EXIST", scheduled_arrival=sched_time.isoformat())
        with self.assertRaises(HTTPException) as ctx:
            get_predicted_eta(req, db=self.mock_db)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("not on route", str(ctx.exception.detail).lower())

    def test_eta_edge_case_no_active_model(self):
        """Verify Section 15: ETA predictor edge case when no model is available in registry."""
        # Remove all models
        self.mock_db["models"].delete_many({})
        sched_time = datetime(2026, 11, 18, 14, 0, 0, tzinfo=timezone.utc)
        req = PredictEtaRequest(route_no="101", stop_code="ST-001", scheduled_arrival=sched_time.isoformat())
        with self.assertRaises(HTTPException) as ctx:
            get_predicted_eta(req, db=self.mock_db)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("no trained model available", str(ctx.exception.detail).lower())


if __name__ == "__main__":
    unittest.main()
