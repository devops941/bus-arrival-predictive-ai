"""
Model Registry & Training API Router.
Handles training jobs (background worker), leaderboards, model activation, and rollback.
Only administrators may activate or rollback models.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from pydantic import BaseModel, Field

from backend.deps import require_role, get_current_user, get_db
from src.ml.models import create_model_instance
from src.ml.validate import run_training_pipeline
from src.ml.features import extract_features_dataset
from src.db.repositories.model_repo import ModelRepository
from src.db.repositories.route_repo import RouteRepository, StopRepository, RouteStopRepository
from src.db.repositories.trip_repo import TripRepository
from src.db.repositories.observation_repo import ObservationRepository, DelayEventRepository
from src.db.repositories.audit_repo import AuditRepository


router = APIRouter(prefix="/models", tags=["Model Registry"])


class TrainModelRequest(BaseModel):
    algorithm: str = Field(default="quantile_gb", description="Algorithm: baseline, ridge, random_forest, gradient_boosting, quantile_gb")
    random_seed: int = 42


def background_train_task(
    job_id: str,
    algorithm: str,
    random_seed: int,
    user_id: str,
    user_email: str,
    db: Any,
):
    """Background execution worker for model training."""
    jobs_coll = db["job_runs"]
    model_repo = ModelRepository(db)
    audit_repo = AuditRepository(db)

    try:
        jobs_coll.update_one(
            {"job_id": job_id},
            {"$set": {"status": "running", "started_at": datetime.now(timezone.utc)}}
        )

        route_repo = RouteRepository(db)
        stop_repo = StopRepository(db)
        rs_repo = RouteStopRepository(db)
        trip_repo = TripRepository(db)
        obs_repo = ObservationRepository(db)
        event_repo = DelayEventRepository(db)

        routes = route_repo.find_many({}, limit=1000)
        stops = stop_repo.find_many({}, limit=2000)
        route_stops = rs_repo.find_many({}, limit=5000)
        trips = trip_repo.find_many({}, limit=10000)
        observations = obs_repo.find_many({}, limit=25000)
        events = event_repo.find_many({}, limit=500)

        df = extract_features_dataset(
            routes=routes,
            stops=stops,
            route_stops=route_stops,
            trips=trips,
            observations=observations,
            delay_events=events,
        )

        model_id = f"mod_{uuid.uuid4().hex[:12]}"
        model_doc = run_training_pipeline(
            algorithm=algorithm,
            feature_df=df,
            model_id=model_id,
            created_by=user_email,
            random_seed=random_seed,
        )

        model_repo.insert_one(model_doc)

        jobs_coll.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": "completed",
                    "model_id": model_id,
                    "metrics": model_doc["metrics"],
                    "beats_baseline": model_doc["beats_baseline"],
                    "completed_at": datetime.now(timezone.utc),
                }
            }
        )

        audit_repo.log_event(
            action="MODEL_TRAINED",
            entity_type="model",
            entity_id=model_id,
            user_id=user_id,
            user_email=user_email,
            details={
                "algorithm": algorithm,
                "mae": model_doc["metrics"]["mae"],
                "beats_baseline": model_doc["beats_baseline"],
            },
        )
    except Exception as exc:
        jobs_coll.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": "failed",
                    "error": str(exc),
                    "failed_at": datetime.now(timezone.utc),
                }
            }
        )


@router.post("/train", status_code=status.HTTP_202_ACCEPTED)
def train_model(
    payload: TrainModelRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role(["analyst", "admin"])),
    db=Depends(get_db),
):
    """
    Launch asynchronous model training pipeline as a background task.
    Returns tracking job_id for polling status.
    """
    job_id = f"job_tr_{uuid.uuid4().hex[:10]}"
    jobs_coll = db["job_runs"]
    jobs_coll.insert_one({
        "job_id": job_id,
        "algorithm": payload.algorithm,
        "status": "pending",
        "created_by": current_user["email"],
        "created_at": datetime.now(timezone.utc),
    })

    background_tasks.add_task(
        background_train_task,
        job_id=job_id,
        algorithm=payload.algorithm,
        random_seed=payload.random_seed,
        user_id=current_user["id"],
        user_email=current_user["email"],
        db=db,
    )

    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"Training job '{job_id}' queued successfully.",
    }


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str, db=Depends(get_db)):
    """Poll background model training job status."""
    job = db["job_runs"].find_one({"job_id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail={"detail": "Training job not found", "code": "NOT_FOUND"})
    if "_id" in job:
        job["id"] = str(job["_id"])
        job["_id"] = str(job["_id"])
    return job


@router.get("")
def list_models(
    status_filter: Optional[str] = Query(None, description="candidate, active, or archived"),
    db=Depends(get_db),
):
    """List all registered ML models with evaluation metrics."""
    model_repo = ModelRepository(db)
    query = {"status": status_filter} if status_filter else {}
    return model_repo.find_many(query, limit=100, sort=[("created_at", -1)])


@router.get("/compare")
def compare_models(db=Depends(get_db)):
    """Compare performance metrics of all candidate and active models against baselines."""
    model_repo = ModelRepository(db)
    all_models = model_repo.find_many({}, limit=100, sort=[("created_at", -1)])

    comparison_table = []
    for m in all_models:
        metrics = m.get("metrics", {})
        base_metrics = m.get("baseline_metrics", {})
        mae = metrics.get("mae", 0.0)
        base_mae = base_metrics.get("mae", 0.0)
        improvement_pct = round(((base_mae - mae) / base_mae) * 100.0, 1) if base_mae > 0 else 0.0

        comparison_table.append({
            "model_id": m.get("model_id"),
            "name": m.get("name"),
            "algorithm": m.get("algorithm"),
            "status": m.get("status"),
            "mae": mae,
            "rmse": metrics.get("rmse", 0.0),
            "within_2_min_pct": metrics.get("within_2_min_pct", 0.0),
            "bias": metrics.get("bias", 0.0),
            "p90_coverage_pct": metrics.get("p90_coverage_pct", 0.0),
            "baseline_mae": base_mae,
            "improvement_pct": improvement_pct,
            "beats_baseline": m.get("beats_baseline", False),
            "created_at": m.get("created_at"),
        })

    return comparison_table


@router.get("/{id}")
def get_model_details(id: str, db=Depends(get_db)):
    """Retrieve complete metadata, feature importances, and error distributions for a model."""
    model_repo = ModelRepository(db)
    m = model_repo.get_by_model_id(id)
    if not m:
        raise HTTPException(status_code=404, detail={"detail": "Model not found", "code": "NOT_FOUND"})
    return m


@router.post("/{id}/activate")
def activate_model_endpoint(
    id: str,
    current_admin: dict = Depends(require_role(["admin"])),
    db=Depends(get_db),
):
    """Administrator activates candidate model for live production ETA serving."""
    model_repo = ModelRepository(db)
    audit_repo = AuditRepository(db)

    success = model_repo.activate_model(id)
    if not success:
        raise HTTPException(status_code=404, detail={"detail": "Model not found", "code": "NOT_FOUND"})

    audit_repo.log_event(
        action="MODEL_ACTIVATED",
        entity_type="model",
        entity_id=id,
        user_id=current_admin["id"],
        user_email=current_admin["email"],
        details={"status": "active"},
    )
    return {"detail": f"Model '{id}' is now active in production.", "model_id": id}


@router.post("/rollback")
def rollback_model_endpoint(
    current_admin: dict = Depends(require_role(["admin"])),
    db=Depends(get_db),
):
    """Administrator rolls back production to previously archived model."""
    model_repo = ModelRepository(db)
    audit_repo = AuditRepository(db)

    active = model_repo.rollback_model()
    if not active:
        raise HTTPException(status_code=400, detail={"detail": "No previous archived model available for rollback", "code": "NO_PREVIOUS_MODEL"})

    audit_repo.log_event(
        action="MODEL_ROLLED_BACK",
        entity_type="model",
        entity_id=active["model_id"],
        user_id=current_admin["id"],
        user_email=current_admin["email"],
        details={"rolled_back_to": active["model_id"]},
    )
    return {"detail": f"Rolled back to model '{active['model_id']}'", "active_model": active}
