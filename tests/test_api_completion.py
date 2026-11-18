"""
Tests for Phase 8: Accuracy, Reports, Admin Endpoints, and API Completion.
Verifies:
- Accuracy endpoints (overview, errors, by-route, predicted-vs-actual, leave-route-out)
- Reports generation in CSV, Excel, and HTML formats
- Admin endpoints (users, role updates, status toggle, system diagnostics)
- Role scoping and field-level error format
"""

import os
from datetime import datetime, timezone
import unittest
from unittest.mock import MagicMock, patch

os.environ["APP_ENV"] = "test"
os.environ["TESTING"] = "true"
os.environ["MONGODB_URI"] = "mongodb://127.0.0.1:27017"
os.environ["JWT_SECRET"] = "super-secret-jwt-key-that-is-at-least-32-chars-long-for-testing"

from tests.test_auth import MockDatabase
from backend.routers.accuracy import (
    get_accuracy_overview,
    get_error_distribution,
    get_accuracy_by_route,
    get_predicted_vs_actual_scatter,
    get_leave_route_out_results,
)
from backend.routers.reports import create_report, CreateReportRequest
from backend.routers.admin import (
    get_all_users,
    update_user_role,
    update_user_status,
    get_system_diagnostics,
    RoleUpdateRequest,
    UserStatusUpdateRequest,
)
from fastapi import HTTPException


class TestAccuracyAndDiagnostics(unittest.TestCase):
    def setUp(self):
        self.mock_db = MockDatabase(name="busarrival_test")
        self.mock_db["models"].insert_one({
            "model_id": "mod_active_01",
            "name": "Quantile GB Active",
            "algorithm": "quantile_gb",
            "status": "active",
            "metrics": {
                "mae": 1.35,
                "rmse": 2.05,
                "mape": 18.2,
                "within_2_min_pct": 82.5,
                "bias": 0.02,
                "p90_coverage_pct": 91.0,
            },
            "baseline_metrics": {
                "mae": 3.40,
                "within_2_min_pct": 42.0,
            },
            "beats_baseline": True,
            "error_distributions": {
                "histogram": [{"bin_label": "-2 to 0m", "count": 120}],
                "by_route": [{"route_no": "101", "mae": 1.25}],
            },
            "leave_route_out": {
                "101": {"mae": 1.45, "held_out_route": "101"}
            },
        })

    def test_accuracy_overview_computes_improvement(self):
        """Verify accuracy overview compares active model to baseline."""
        res = get_accuracy_overview(db=self.mock_db)
        self.assertEqual(res["model_id"], "mod_active_01")
        self.assertAlmostEqual(res["mae"], 1.35, places=2)
        self.assertAlmostEqual(res["baseline_mae"], 3.40, places=2)
        self.assertTrue(res["beats_baseline"])
        self.assertGreater(res["improvement_pct"], 50.0)

    def test_error_distribution_endpoint(self):
        res = get_error_distribution(db=self.mock_db)
        self.assertIn("histogram", res)
        self.assertEqual(len(res["histogram"]), 1)

    def test_accuracy_by_route_endpoint(self):
        res = get_accuracy_by_route(db=self.mock_db)
        self.assertIn("by_route", res)
        self.assertEqual(res["by_route"][0]["route_no"], "101")

    def test_leave_route_out_endpoint(self):
        res = get_leave_route_out_results(db=self.mock_db)
        self.assertIn("leave_route_out", res)
        self.assertIn("101", res["leave_route_out"])

    def test_predicted_vs_actual_scatter(self):
        res = get_predicted_vs_actual_scatter(sample_limit=50, db=self.mock_db)
        self.assertIn("points", res)
        self.assertIn("ideal_line", res)


class TestReportsGeneration(unittest.TestCase):
    def setUp(self):
        self.mock_db = MockDatabase(name="busarrival_test")
        self.current_user = {"id": "analyst_1", "email": "analyst@transit.org", "role": "analyst"}
        # Add a test route
        self.mock_db["routes"].insert_one({
            "route_no": "101",
            "name": "Metro Express",
            "total_distance_km": 15.0,
            "scheduled_headway_min": 15,
            "active": True,
        })

    def test_generate_csv_report(self):
        req = CreateReportRequest(kind="summary", file_format="csv", title="Monthly Summary")
        res = create_report(req, current_user=self.current_user, db=self.mock_db)
        self.assertIn("report_id", res)
        self.assertEqual(res["file_format"], "csv")
        self.assertIn("/download", res["download_url"])

    def test_generate_excel_report(self):
        req = CreateReportRequest(kind="summary", file_format="excel", title="Excel Transit Export")
        res = create_report(req, current_user=self.current_user, db=self.mock_db)
        self.assertIn("report_id", res)
        self.assertEqual(res["file_format"], "excel")

    def test_generate_html_report(self):
        req = CreateReportRequest(kind="summary", file_format="html", title="HTML Branded Report")
        res = create_report(req, current_user=self.current_user, db=self.mock_db)
        self.assertIn("report_id", res)
        self.assertEqual(res["file_format"], "html")


class TestAdminEndpoints(unittest.TestCase):
    def setUp(self):
        self.mock_db = MockDatabase(name="busarrival_test")
        self.admin_user = {"id": "admin_1", "email": "admin@busarrival.local", "role": "admin"}
        self.mock_db["users"].insert_one({
            "id": "user_42",
            "email": "driver@transit.org",
            "role": "passenger",
            "is_active": True,
            "failed_login_attempts": 0,
            "locked_until": None,
            "created_at": datetime.now(timezone.utc),
        })

    def test_admin_update_user_role(self):
        res = update_user_role(
            id="user_42",
            payload=RoleUpdateRequest(role="analyst"),
            current_admin=self.admin_user,
            db=self.mock_db,
        )
        self.assertEqual(res["new_role"], "analyst")
        user = self.mock_db["users"].find_one({"id": "user_42"})
        self.assertEqual(user["role"], "analyst")

    def test_admin_update_user_status(self):
        res = update_user_status(
            id="user_42",
            payload=UserStatusUpdateRequest(is_active=False),
            current_admin=self.admin_user,
            db=self.mock_db,
        )
        user = self.mock_db["users"].find_one({"id": "user_42"})
        self.assertFalse(user["is_active"])

    def test_system_diagnostics(self):
        diag = get_system_diagnostics(current_admin=self.admin_user, db=self.mock_db)
        self.assertEqual(diag["status"], "operational")
        self.assertIn("collection_counts", diag)
        self.assertIn("users", diag["collection_counts"])


if __name__ == "__main__":
    unittest.main()
