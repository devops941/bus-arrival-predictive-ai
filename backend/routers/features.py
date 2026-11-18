"""
Feature Pipeline API Router.
Builds, caches, and previews machine learning feature matrices.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.deps import require_role, get_db
from src.ml.features import extract_features_dataset, FEATURE_COLUMNS
from src.db.repositories.route_repo import RouteRepository, StopRepository, RouteStopRepository
from src.db.repositories.trip_repo import TripRepository
from src.db.repositories.observation_repo import ObservationRepository, DelayEventRepository
from src.db.repositories.feature_repo import FeatureCacheRepository
from src.db.repositories.audit_repo import AuditRepository


router = APIRouter(prefix="/features", tags=["Feature Pipeline"])


class FeatureBuildResponse(BaseModel):
    data_version: int
    total_rows: int
    feature_count: int
    feature_names: List[str]
    sample_preview: List[Dict[str, Any]]
    created_at: datetime


@router.post("/build", response_model=FeatureBuildResponse)
def build_features_endpoint(
    current_user: dict = Depends(require_role(["analyst", "admin"])),
    db=Depends(get_db),
):
    """
    Execute feature engineering pipeline on MongoDB transit data.
    Stores metadata in features_cache and returns a data preview.
    """
    route_repo = RouteRepository(db)
    stop_repo = StopRepository(db)
    rs_repo = RouteStopRepository(db)
    trip_repo = TripRepository(db)
    obs_repo = ObservationRepository(db)
    event_repo = DelayEventRepository(db)
    feature_repo = FeatureCacheRepository(db)
    audit_repo = AuditRepository(db)

    routes = route_repo.find_many({}, limit=1000)
    stops = stop_repo.find_many({}, limit=2000)
    route_stops = rs_repo.find_many({}, limit=5000)
    trips = trip_repo.find_many({}, limit=10000)
    observations = obs_repo.find_many({}, limit=25000)
    events = event_repo.find_many({}, limit=500)

    if not observations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "No observations found in database. Seed data first.", "code": "NO_DATA"},
        )

    # Vectorize features
    df = extract_features_dataset(
        routes=routes,
        stops=stops,
        route_stops=route_stops,
        trips=trips,
        observations=observations,
        delay_events=events,
    )

    latest_cache = feature_repo.get_latest_cache()
    new_version = (latest_cache.get("data_version", 0) + 1) if latest_cache else 1

    preview_records = df.head(10).to_dict(orient="records")
    # Clean datetime objects for JSON serialization
    for row in preview_records:
        for k, v in row.items():
            if isinstance(v, datetime):
                row[k] = v.isoformat()

    feature_repo.cache_features_metadata(
        data_version=new_version,
        feature_count=len(df),
        feature_names=FEATURE_COLUMNS,
        sample_preview=preview_records,
    )

    audit_repo.log_event(
        action="FEATURES_BUILT",
        entity_type="features_cache",
        user_id=current_user["id"],
        user_email=current_user["email"],
        details={"data_version": new_version, "rows": len(df)},
    )

    return FeatureBuildResponse(
        data_version=new_version,
        total_rows=len(df),
        feature_count=len(FEATURE_COLUMNS),
        feature_names=FEATURE_COLUMNS,
        sample_preview=preview_records,
        created_at=datetime.now(timezone.utc),
    )


@router.get("/preview")
def get_features_preview(db=Depends(get_db)):
    """Retrieve the latest cached features build metadata and sample records."""
    feature_repo = FeatureCacheRepository(db)
    cache = feature_repo.get_latest_cache()
    if not cache:
        return {
            "data_version": 0,
            "total_rows": 0,
            "feature_names": FEATURE_COLUMNS,
            "sample_preview": [],
            "message": "No feature builds cached yet. Call POST /api/features/build.",
        }
    return cache
