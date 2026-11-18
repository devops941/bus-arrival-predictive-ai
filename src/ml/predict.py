"""
BusArrival AI - Real-time ETA Prediction and Drift Monitoring Service
Implements Section 7.5 & 7.6:
- Predicts ETA P50, ETA P90, expected delay, and reliability label
- Logs predictions into predictions_log
- Evaluates real-time delays along entire route corridor
- Performs model drift checks against DRIFT_RATIO_THRESHOLD
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from src.config import get_settings
from src.ml.features import build_feature_row, FEATURE_COLUMNS
from src.ml.models import load_model_artifact, QuantileGBModel
from src.db.repositories.model_repo import ModelRepository
from src.db.repositories.route_repo import RouteRepository, RouteStopRepository
from src.db.repositories.observation_repo import ObservationRepository, DelayEventRepository
from src.db.repositories.prediction_repo import PredictionRepository, AlertRepository


DISCLAIMER = "Estimate based on recent traffic & route historical delays, not a guarantee."


def calculate_reliability_label(
    interval_width: float,
    validation_mae: float
) -> str:
    """
    Determine ETA reliability tier:
    - HIGH: Interval <= 4.0 min and route validation MAE <= 2.0 min
    - MEDIUM: Interval <= 8.0 min
    - LOW: Interval > 8.0 min or high historical error variance
    """
    if interval_width <= 4.0 and validation_mae <= 2.0:
        return "HIGH"
    elif interval_width <= 8.0:
        return "MEDIUM"
    return "LOW"


def predict_eta(
    route_no: str,
    stop_code: str,
    scheduled_time: datetime,
    db: Any,
    precipitation_mm: float = 0.0,
    recent_corridor_delay: float = 0.0,
) -> Dict[str, Any]:
    """
    Generate confidence-banded ETA prediction for a given route and stop.
    """
    if scheduled_time.tzinfo is None:
        scheduled_time = scheduled_time.replace(tzinfo=timezone.utc)

    route_repo = RouteRepository(db)
    rs_repo = RouteStopRepository(db)
    obs_repo = ObservationRepository(db)
    event_repo = DelayEventRepository(db)
    model_repo = ModelRepository(db)
    pred_repo = PredictionRepository(db)

    # 1. Fetch active model
    active_model_doc = model_repo.get_active_model()
    if not active_model_doc:
        # Fall back to any candidate or baseline
        models = model_repo.find_many({}, limit=1, sort=[("created_at", -1)])
        active_model_doc = models[0] if models else None

    if not active_model_doc or not active_model_doc.get("artifact_path"):
        raise ValueError("No trained model available in model registry. Train a model first via /api/models/train.")

    # 2. Fetch route and stop specs
    route = route_repo.get_by_route_no(route_no)
    if not route:
        raise ValueError(f"Route '{route_no}' not found in database.")

    corridor_stops = rs_repo.get_stops_for_route(route_no)
    target_rs = next((rs for rs in corridor_stops if rs["stop_code"] == stop_code), None)
    if not target_rs:
        raise ValueError(f"Stop code '{stop_code}' is not on Route '{route_no}'.")

    max_sequence = max((int(rs["sequence"]) for rs in corridor_stops), default=8)

    # 3. Fetch past observations strictly prior to scheduled_time
    past_obs = obs_repo.find_many(
        {"scheduled_arrival": {"$lt": scheduled_time}},
        limit=500,
        sort=[("scheduled_arrival", -1)]
    )

    past_events = event_repo.find_many(
        {"date": {"$lte": scheduled_time.strftime("%Y-%m-%d")}},
        limit=50
    )

    # 4. Construct feature vector
    features = build_feature_row(
        route=route,
        route_stop=target_rs,
        max_sequence=max_sequence,
        prediction_time=scheduled_time,
        past_observations=past_obs,
        past_events=past_events,
    )

    # Apply real-time condition shock inputs
    if precipitation_mm > 0.0:
        features["rain_flag"] = 1

    if recent_corridor_delay > 0.0:
        features["recent_route_delay_mean"] = max(features.get("recent_route_delay_mean", 0.0), recent_corridor_delay)
        features["prev_trip_delay"] = max(features.get("prev_trip_delay", 0.0), recent_corridor_delay)

    # 5. Load model artifact and infer
    artifact = load_model_artifact(active_model_doc["artifact_path"])
    model_obj = artifact["model"]

    feature_vector = np.array([[features[col] for col in FEATURE_COLUMNS]], dtype=float)

    if isinstance(model_obj, QuantileGBModel):
        p50_preds, p90_preds = model_obj.predict_intervals(feature_vector)
        pred_delay_p50 = float(p50_preds[0])
        pred_delay_p90 = float(p90_preds[0])
    else:
        pred = float(model_obj.predict(feature_vector)[0])
        pred_delay_p50 = pred
        pred_delay_p90 = pred + 3.0  # approximate boundary for point estimators

    # Apply physical shock additions for live weather / corridor traffic delays
    if precipitation_mm > 0.0:
        rain_delay_add = 3.0 + round((precipitation_mm / 10.0), 1)
        pred_delay_p50 += rain_delay_add
        pred_delay_p90 += rain_delay_add * 1.35

    if recent_corridor_delay > 0.0:
        pred_delay_p50 += recent_corridor_delay
        pred_delay_p90 += recent_corridor_delay * 1.25

    # Round delays
    delay_p50 = round(pred_delay_p50, 1)
    delay_p90 = round(max(pred_delay_p90, delay_p50), 1)

    eta_p50 = scheduled_time + timedelta(minutes=delay_p50)
    eta_p90 = scheduled_time + timedelta(minutes=delay_p90)
    interval_width = round(delay_p90 - delay_p50, 1)

    route_val_mae = active_model_doc.get("metrics", {}).get("mae", 2.0)
    reliability = calculate_reliability_label(interval_width, route_val_mae)

    # 6. Log prediction
    prediction_id = pred_repo.log_prediction(
        route_no=route_no,
        stop_code=stop_code,
        scheduled_time=scheduled_time,
        eta_p50=eta_p50,
        eta_p90=eta_p90,
        delay_p50_min=delay_p50,
        delay_p90_min=delay_p90,
        reliability=reliability,
        model_id=active_model_doc["model_id"],
    )

    return {
        "prediction_id": prediction_id,
        "route_no": route_no,
        "stop_code": stop_code,
        "scheduled_time": scheduled_time.isoformat(),
        "eta_p50": eta_p50.isoformat(),
        "eta_p90": eta_p90.isoformat(),
        "expected_delay_min": delay_p50,
        "p90_delay_min": delay_p90,
        "interval_width_min": interval_width,
        "reliability": reliability,
        "model_id": active_model_doc["model_id"],
        "model_name": active_model_doc.get("name", "Active Model"),
        "disclaimer": DISCLAIMER,
    }


def predict_route_corridor(
    route_no: str,
    scheduled_departure: datetime,
    db: Any,
) -> List[Dict[str, Any]]:
    """
    Compute ETA predictions for every stop along the route corridor.
    """
    rs_repo = RouteStopRepository(db)
    corridor_stops = rs_repo.get_stops_for_route(route_no)

    corridor_results = []
    for rs in corridor_stops:
        offset = timedelta(minutes=int(rs.get("scheduled_offset_min", 0)))
        stop_sched_time = scheduled_departure + offset
        try:
            pred = predict_eta(
                route_no=route_no,
                stop_code=rs["stop_code"],
                scheduled_time=stop_sched_time,
                db=db,
            )
            corridor_results.append({
                "sequence": rs.get("sequence", 1),
                "stop_code": rs["stop_code"],
                "distance_from_start_km": rs.get("distance_from_start_km", 0.0),
                "scheduled_arrival": stop_sched_time.isoformat(),
                "eta_p50": pred["eta_p50"],
                "expected_delay_min": pred["expected_delay_min"],
                "reliability": pred["reliability"],
            })
        except Exception:
            continue

    return corridor_results


def check_and_create_drift_alerts(db: Any) -> List[Dict[str, Any]]:
    """
    Section 7.6 Drift Monitoring:
    Compares recent rolling MAE with active model validation MAE.
    Raises alert when rolling MAE exceeds threshold ratio.
    """
    settings = get_settings()
    model_repo = ModelRepository(db)
    obs_repo = ObservationRepository(db)
    alert_repo = AlertRepository(db)

    active_model = model_repo.get_active_model()
    if not active_model:
        return []

    validation_mae = float(active_model.get("metrics", {}).get("mae", 2.0))
    if validation_mae <= 0.01:
        validation_mae = 1.0

    recent_obs = obs_repo.find_many({}, limit=200, sort=[("scheduled_arrival", -1)])
    if len(recent_obs) < 20:
        return []

    delays = [abs(float(o.get("delay_min", 0.0))) for o in recent_obs if "delay_min" in o]
    rolling_mae = float(np.mean(delays))

    drift_ratio = rolling_mae / validation_mae
    alerts = []
    if drift_ratio >= settings.DRIFT_RATIO_THRESHOLD:
        alert_id = alert_repo.create_drift_alert(
            model_id=active_model["model_id"],
            current_mae=rolling_mae,
            validation_mae=validation_mae,
            drift_ratio=drift_ratio,
        )
        alerts.append({
            "alert_id": alert_id,
            "drift_ratio": drift_ratio,
            "current_mae": rolling_mae,
            "validation_mae": validation_mae,
        })

    return alerts
