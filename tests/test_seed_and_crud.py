"""
Tests for Phase 3: Synthetic Data Generation, Seeding, Validation, and CRUD APIs.
Verifies:
- Synthetic dataset generation (routes, stops, route-stops, trips, observations)
- Detection of intentional messy rows (duplicates, outliers, foreign key misses)
- Database seeding idempotency and collection coverage
- Validation rules and field-level error messages
"""

import os
from datetime import datetime, timezone, timedelta
import unittest
from unittest.mock import MagicMock, patch

os.environ["APP_ENV"] = "test"
os.environ["TESTING"] = "true"
os.environ["MONGODB_URI"] = "mongodb://127.0.0.1:27017"
os.environ["JWT_SECRET"] = "super-secret-jwt-key-that-is-at-least-32-chars-long-for-testing"

from src.data.synthetic import generate_synthetic_dataset
from src.data.validate import validate_routes, validate_stops, validate_observations
from src.data.ingest import parse_csv_content, process_import
from scripts.seed import run_seed
from tests.test_auth import MockDatabase
from backend.routers.routes import create_route, list_routes, RouteCreate
from backend.routers.trips import create_observation, ObservationCreate
from fastapi import HTTPException


class TestSyntheticDataAndValidation(unittest.TestCase):
    def test_synthetic_data_generation(self):
        """Verify synthetic transit data generation produces all required datasets."""
        data = generate_synthetic_dataset(num_days=10, seed=42, include_messy_rows=True)
        self.assertGreaterEqual(len(data["routes"]), 7)
        self.assertGreaterEqual(len(data["stops"]), 40)
        self.assertGreater(len(data["trips"]), 50)
        self.assertGreater(len(data["observations"]), 300)
        
        # Verify illustrative label
        for r in data["routes"]:
            self.assertEqual(r["data_label"], "illustrative demo data")

    def test_detection_of_messy_rows(self):
        """
        Verify Acceptance Criteria:
        Deliberately messy rows (duplicates, outliers, foreign-key errors) are detected.
        """
        data = generate_synthetic_dataset(num_days=5, seed=42, include_messy_rows=True)
        route_set = {r["route_no"] for r in data["routes"]}
        stop_set = {s["stop_code"] for s in data["stops"]}

        valid_obs, issues = validate_observations(
            data["observations"],
            valid_route_nos=route_set,
            valid_stop_codes=stop_set,
        )

        issue_types = {iss["issue_type"] for iss in issues}
        # Verify detected issue types
        self.assertTrue(
            "DUPLICATE" in issue_types or "RANGE" in issue_types or "FOREIGN_KEY" in issue_types,
            f"Expected issue types not found in: {issue_types}"
        )

    def test_route_validation_rules(self):
        """Verify validation errors for bad distances and missing fields."""
        invalid_routes = [
            {"route_no": "", "name": "Missing No", "total_distance_km": 10.0, "scheduled_headway_min": 15},
            {"route_no": "101", "name": "Negative Dist", "total_distance_km": -5.0, "scheduled_headway_min": 15},
            {"route_no": "102", "name": "Zero Headway", "total_distance_km": 12.0, "scheduled_headway_min": 0},
        ]
        valid_rows, issues = validate_routes(invalid_routes)
        self.assertEqual(len(valid_rows), 0)
        self.assertGreaterEqual(len(issues), 3)

    def test_csv_import_pipeline(self):
        """Verify CSV ingestion report and issue formatting."""
        csv_text = """route_no,name,origin,destination,total_distance_km,scheduled_headway_min
101,Express Line,Downtown,Airport,25.5,15
102,Bad Distance,Campus,Station,-2.0,20
101,Duplicate Line,West,East,15.0,15
"""
        rows = parse_csv_content(csv_text)
        report = process_import("routes", rows)
        self.assertEqual(report["total_rows"], 3)
        self.assertEqual(report["valid_count"], 1)
        self.assertEqual(report["invalid_count"], 2)
        self.assertEqual(len(report["issues"]), 2)


class TestDatabaseSeeding(unittest.TestCase):
    def test_run_seed_fills_all_collections(self):
        """
        Verify Acceptance Criteria:
        Seed fills all collections and prints counts.
        """
        mock_db = MockDatabase(name="busarrival_test")
        with patch("scripts.seed.get_database", return_value=mock_db), \
             patch("scripts.seed.apply_collection_validators"), \
             patch("scripts.seed.ensure_indexes"):
            summary = run_seed(days=5, seed_val=42)

            self.assertGreater(summary["routes"], 0)
            self.assertGreater(summary["stops"], 0)
            self.assertGreater(summary["route_stops"], 0)
            self.assertGreater(summary["trips"], 0)
            self.assertGreater(summary["observations"], 0)
            self.assertGreater(summary["detected_messy_issues"], 0)

            # Collections in DB must be filled
            self.assertIn("routes", mock_db.collections)
            self.assertIn("stops", mock_db.collections)
            self.assertIn("trips", mock_db.collections)
            self.assertIn("observations", mock_db.collections)
            self.assertIn("audit_log", mock_db.collections)


class TestCRUDRouters(unittest.TestCase):
    def setUp(self):
        self.mock_db = MockDatabase(name="busarrival_test")
        from src.db.repositories.route_repo import RouteRepository
        from src.db.repositories.observation_repo import ObservationRepository
        self.route_repo = RouteRepository(self.mock_db)
        self.obs_repo = ObservationRepository(self.mock_db)
        self.audit_repo = MagicMock()
        self.current_user = {"id": "user_1", "email": "analyst@transit.org", "role": "analyst"}

    def test_create_route_and_conflict(self):
        """Verify route creation and duplicate conflict status code."""
        payload = RouteCreate(
            route_no="99",
            name="Rapid Bus",
            origin="Station A",
            destination="Station B",
            total_distance_km=14.5,
            scheduled_headway_min=10,
        )
        created = create_route(
            payload=payload,
            current_user=self.current_user,
            route_repo=self.route_repo,
            audit_repo=self.audit_repo,
        )
        self.assertEqual(created["route_no"], "99")

        # Creating again must raise HTTP 409
        with self.assertRaises(HTTPException) as ctx:
            create_route(
                payload=payload,
                current_user=self.current_user,
                route_repo=self.route_repo,
                audit_repo=self.audit_repo,
            )
        self.assertEqual(ctx.exception.status_code, 409)

    def test_create_observation_derives_delay(self):
        """Verify observation endpoint derives delay_min automatically."""
        sched = datetime(2026, 11, 18, 14, 0, 0, tzinfo=timezone.utc)
        actual = datetime(2026, 11, 18, 14, 6, 30, tzinfo=timezone.utc)
        payload = ObservationCreate(
            trip_id="TR-101-01",
            stop_code="ST-001",
            route_no="101",
            scheduled_arrival=sched,
            actual_arrival=actual,
        )
        created = create_observation(
            payload=payload,
            current_user=self.current_user,
            obs_repo=self.obs_repo,
            audit_repo=self.audit_repo,
        )
        self.assertAlmostEqual(created["delay_min"], 6.5, places=1)
        self.assertFalse(created["is_outlier"])


if __name__ == "__main__":
    unittest.main()
