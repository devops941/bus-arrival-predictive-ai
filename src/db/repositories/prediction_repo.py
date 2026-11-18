"""
Prediction Log and Drift Alert Repositories for MongoDB.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pymongo.database import Database
from src.db.repositories.base import BaseRepository


class PredictionRepository(BaseRepository):
    def __init__(self, db: Optional[Database] = None):
        super().__init__("predictions_log", db)

    def log_prediction(
        self,
        route_no: str,
        stop_code: str,
        scheduled_time: datetime,
        eta_p50: datetime,
        eta_p90: datetime,
        delay_p50_min: float,
        delay_p90_min: float,
        reliability: str,
        model_id: str,
    ) -> str:
        doc = {
            "route_no": str(route_no).strip(),
            "stop_code": str(stop_code).strip(),
            "scheduled_time": scheduled_time,
            "eta_p50": eta_p50,
            "eta_p90": eta_p90,
            "delay_p50_min": delay_p50_min,
            "delay_p90_min": delay_p90_min,
            "interval_width_min": round(delay_p90_min - delay_p50_min, 2),
            "reliability": reliability,
            "model_id": model_id,
            "actual_arrival": None,
            "actual_delay_min": None,
            "created_at": datetime.now(timezone.utc),
        }
        return self.insert_one(doc)


class AlertRepository(BaseRepository):
    def __init__(self, db: Optional[Database] = None):
        super().__init__("alerts", db)

    def create_drift_alert(
        self,
        model_id: str,
        current_mae: float,
        validation_mae: float,
        drift_ratio: float,
        route_no: Optional[str] = None,
    ) -> str:
        severity = "high" if drift_ratio >= 1.6 else "medium" if drift_ratio >= 1.3 else "low"
        doc = {
            "alert_type": "MODEL_DRIFT",
            "severity": severity,
            "model_id": model_id,
            "route_no": route_no,
            "current_mae": round(current_mae, 2),
            "validation_mae": round(validation_mae, 2),
            "drift_ratio": round(drift_ratio, 2),
            "message": f"Model MAE degraded to {current_mae:.2f}m ({drift_ratio:.2f}x validation baseline of {validation_mae:.2f}m)",
            "status": "open",
            "is_resolved": False,
            "created_at": datetime.now(timezone.utc),
        }
        return self.insert_one(doc)

    def list_open_alerts(self) -> List[Dict[str, Any]]:
        return self.find_many({"$or": [{"status": "open"}, {"is_resolved": False}]}, sort=[("created_at", -1)])

    def list_all_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.find_many({}, limit=limit, sort=[("created_at", -1)])

    def resolve_alert(self, alert_id: str) -> bool:
        from bson import ObjectId
        query_list = [{"id": alert_id}, {"alert_id": alert_id}]
        try:
            query_list.append({"_id": ObjectId(alert_id)})
        except Exception:
            pass
        return self.collection.update_many(
            {"$or": query_list},
            {"$set": {"status": "resolved", "is_resolved": True, "resolved_at": datetime.now(timezone.utc)}}
        ).modified_count > 0
