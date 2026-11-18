"""
ETA Prediction & Real-time Transit Serving API Router.
Exposes confidence-banded arrival predictions and corridor delay diagrams.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.deps import get_db, require_role
from src.ml.predict import (
    predict_eta,
    predict_route_corridor,
    check_and_create_drift_alerts,
)
from src.db.repositories.prediction_repo import AlertRepository, PredictionRepository
from src.db.repositories.route_repo import RouteRepository, StopRepository


router = APIRouter(prefix="/predict", tags=["ETA Predictor"])


class PredictEtaRequest(BaseModel):
    route_no: Optional[str] = Field(None, description="Route identifier, e.g. '101'")
    route_id: Optional[str] = Field(None, description="Route ID or route_no")
    stop_code: Optional[str] = Field(None, description="Stop code, e.g. 'ST-001'")
    stop_id: Optional[str] = Field(None, description="Stop ID or stop_code")
    scheduled_time: Optional[datetime] = Field(None, description="Scheduled or planned arrival time (defaults to now)")
    scheduled_arrival: Optional[str] = Field(None, description="ISO arrival string")
    precipitation_mm: Optional[float] = 0.0
    recent_corridor_delay: Optional[float] = 0.0


class DelayRange(BaseModel):
    p50: float
    p90: float


class PredictEtaResponse(BaseModel):
    prediction_id: str
    route_no: str
    route_id: Optional[str] = None
    stop_code: str
    stop_id: Optional[str] = None
    stop_name: Optional[str] = None
    scheduled_time: str
    scheduled_arrival: Optional[str] = None
    eta_p50: str
    eta_p90: str
    predicted_arrival_p50: Optional[str] = None
    predicted_arrival_p90: Optional[str] = None
    expected_delay_min: float
    p90_delay_min: float
    interval_width_min: float
    delay_range_min: Optional[DelayRange] = None
    reliability: str
    reliability_tier: Optional[str] = None
    confidence_score: Optional[int] = 88
    model_id: str
    model_name: str
    disclaimer: str


@router.post("/eta", response_model=PredictEtaResponse)
def get_predicted_eta(
    payload: PredictEtaRequest,
    db=Depends(get_db),
):
    """
    Generate confidence-banded ETA prediction (P50 & P90) and reliability badge.
    Logs inference to predictions_log.
    """
    route_param = payload.route_no or payload.route_id
    if not route_param:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "route_no or route_id is required", "code": "PARAM_REQUIRED"}
        )

    route_repo = RouteRepository(db)
    r = route_repo.find_by_id(route_param) or route_repo.get_by_route_no(route_param)
    route_no = r.get("route_no") if r else route_param

    stop_param = payload.stop_code or payload.stop_id
    if not stop_param:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "stop_code or stop_id is required", "code": "PARAM_REQUIRED"}
        )

    stop_repo = StopRepository(db)
    s = stop_repo.find_by_id(stop_param) or stop_repo.get_by_code(stop_param)
    stop_code = s.get("stop_code") if s else stop_param

    target_time = payload.scheduled_time
    if not target_time and payload.scheduled_arrival:
        try:
            target_time = datetime.fromisoformat(payload.scheduled_arrival.replace("Z", "+00:00"))
        except Exception:
            target_time = datetime.now(timezone.utc)
    if not target_time:
        target_time = datetime.now(timezone.utc)

    try:
        result = predict_eta(
            route_no=route_no,
            stop_code=stop_code,
            scheduled_time=target_time,
            db=db,
            precipitation_mm=float(payload.precipitation_mm or 0.0),
            recent_corridor_delay=float(payload.recent_corridor_delay or 0.0),
        )
        result["route_id"] = route_no
        result["stop_id"] = stop_code
        result["stop_name"] = s.get("name") if s else stop_code
        result["scheduled_arrival"] = result["scheduled_time"]
        result["predicted_arrival_p50"] = result["eta_p50"]
        result["predicted_arrival_p90"] = result["eta_p90"]
        result["reliability_tier"] = result["reliability"]
        result["confidence_score"] = 88
        result["delay_range_min"] = DelayRange(
            p50=result["expected_delay_min"],
            p90=result["p90_delay_min"],
        )
        return PredictEtaResponse(**result)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": str(exc), "code": "PREDICTION_FAILED"},
        )


@router.get("/route/{route_no}")
def get_corridor_predictions(
    route_no: str,
    departure_time: Optional[datetime] = Query(None, description="Corridor trip start time"),
    db=Depends(get_db),
):
    """
    Predict arrival times and delays for all stops along a route corridor.
    Feeds the RouteLineDiagram component.
    """
    start_dt = departure_time or datetime.now(timezone.utc)
    return predict_route_corridor(route_no, start_dt, db=db)


@router.post("/drift-check")
def run_drift_check(
    db=Depends(get_db),
):
    """
    Trigger drift monitoring check comparing rolling MAE vs validation baseline.
    Raises alerts if drift exceeds threshold ratio.
    """
    alerts = check_and_create_drift_alerts(db)
    count = len(alerts)
    msg = f"Drift check completed: {count} new alert{'s' if count != 1 else ''} triggered." if count > 0 else "Drift check completed: All corridor models remain within healthy boundaries (drift ratio < 1.3x)."
    return {
        "status": "completed",
        "message": msg,
        "new_alerts_count": count,
        "alerts": alerts,
    }


# Standalone Alerts Router
alerts_router = APIRouter(prefix="/alerts", tags=["Alerts & Drift Monitoring"])


@alerts_router.get("")
def list_alerts(
    status_filter: Optional[str] = Query(None, alias="status"),
    db=Depends(get_db),
):
    """List open system alerts and model drift warnings."""
    alert_repo = AlertRepository(db)
    if status_filter == "open":
        alerts = alert_repo.list_open_alerts()
    else:
        alerts = alert_repo.list_all_alerts(limit=100)

    for a in alerts:
        a["is_resolved"] = (a.get("status") == "resolved" or a.get("is_resolved") is True)
        if not a.get("severity"):
            dr = float(a.get("drift_ratio", 1.0))
            a["severity"] = "high" if dr >= 1.6 else "medium" if dr >= 1.3 else "low"
        if not a.get("created_at"):
            a["created_at"] = datetime.now(timezone.utc).isoformat()
        elif hasattr(a["created_at"], "isoformat"):
            a["created_at"] = a["created_at"].isoformat()

    return alerts


@alerts_router.post("/{alert_id}/resolve")
def resolve_alert_endpoint(
    alert_id: str,
    db=Depends(get_db),
):
    """Resolve/dismiss an active alert."""
    alert_repo = AlertRepository(db)
    success = alert_repo.resolve_alert(alert_id)
    return {"detail": "Alert resolved", "success": success}
