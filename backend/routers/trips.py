"""
Trip, Arrival Observation, and Delay Event Routers.
Handles operational trip recording, arrival observations, and delay event logs.
Audit logs all write actions.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from backend.deps import require_role, get_current_user, get_db
from src.db.repositories.trip_repo import TripRepository
from src.db.repositories.observation_repo import ObservationRepository, DelayEventRepository
from src.db.repositories.audit_repo import AuditRepository


router = APIRouter(tags=["Trips & Observations"])


# Pydantic Schemas
class TripCreate(BaseModel):
    trip_id: str
    route_no: str
    direction: str = "outbound"
    date: str
    scheduled_start: datetime
    vehicle_id: str
    day_type: str = "weekday"


class ObservationCreate(BaseModel):
    trip_id: str
    stop_code: str
    route_no: str
    scheduled_arrival: datetime
    actual_arrival: datetime
    passengers_optional: Optional[int] = None
    weather_optional: Optional[str] = None


class DelayEventCreate(BaseModel):
    route_no: str
    date: str
    time: str
    cause: str = Field(..., description="Reason e.g. traffic, breakdown, rain, event")
    minutes: int = Field(..., gt=0)


# Dependencies
def get_trip_repo(db=Depends(get_db)) -> TripRepository:
    return TripRepository(db)


def get_obs_repo(db=Depends(get_db)) -> ObservationRepository:
    return ObservationRepository(db)


def get_event_repo(db=Depends(get_db)) -> DelayEventRepository:
    return DelayEventRepository(db)


def get_audit_repo(db=Depends(get_db)) -> AuditRepository:
    return AuditRepository(db)


# Trip Endpoints
@router.get("/trips")
def list_trips(
    route_no: Optional[str] = None,
    date_val: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    trip_repo: TripRepository = Depends(get_trip_repo),
):
    query: Dict[str, Any] = {}
    if route_no:
        query["route_no"] = route_no
    if date_val:
        query["date"] = date_val
    return trip_repo.find_many(query, skip=skip, limit=limit, sort=[("scheduled_start", -1)])


@router.post("/trips", status_code=status.HTTP_201_CREATED)
def create_trip(
    payload: TripCreate,
    current_user: dict = Depends(require_role(["analyst", "admin"])),
    trip_repo: TripRepository = Depends(get_trip_repo),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    existing = trip_repo.get_by_trip_id(payload.trip_id)
    if existing:
        raise HTTPException(status_code=409, detail={"detail": f"Trip '{payload.trip_id}' already exists", "code": "TRIP_EXISTS"})

    doc = payload.model_dump()
    doc["created_by"] = current_user["id"]
    doc["created_at"] = datetime.now(timezone.utc)
    t_id = trip_repo.insert_one(doc)

    audit_repo.log_event(
        action="TRIP_CREATED",
        entity_type="trip",
        entity_id=t_id,
        user_id=current_user["id"],
        user_email=current_user["email"],
        details={"trip_id": payload.trip_id},
    )
    doc["id"] = t_id
    return doc


# Observation Endpoints
@router.get("/observations")
def list_observations(
    route_no: Optional[str] = None,
    stop_code: Optional[str] = None,
    trip_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    obs_repo: ObservationRepository = Depends(get_obs_repo),
):
    return obs_repo.get_observations(
        route_no=route_no,
        stop_code=stop_code,
        trip_id=trip_id,
        skip=skip,
        limit=limit,
    )


@router.post("/observations", status_code=status.HTTP_201_CREATED)
def create_observation(
    payload: ObservationCreate,
    current_user: dict = Depends(require_role(["analyst", "admin"])),
    obs_repo: ObservationRepository = Depends(get_obs_repo),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    doc = payload.model_dump()
    delay_min = round((payload.actual_arrival - payload.scheduled_arrival).total_seconds() / 60.0, 2)
    doc["delay_min"] = delay_min
    doc["is_outlier"] = delay_min < -10.0 or delay_min > 120.0
    doc["created_by"] = current_user["id"]
    doc["created_at"] = datetime.now(timezone.utc)

    obs_id = obs_repo.insert_one(doc)
    audit_repo.log_event(
        action="OBSERVATION_CREATED",
        entity_type="observation",
        entity_id=obs_id,
        user_id=current_user["id"],
        user_email=current_user["email"],
        details={"trip_id": payload.trip_id, "delay_min": delay_min},
    )
    doc["id"] = obs_id
    return doc


# Delay Events Endpoints
@router.get("/delay-events")
def list_delay_events(
    route_no: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    event_repo: DelayEventRepository = Depends(get_event_repo),
):
    query = {"route_no": route_no} if route_no else {}
    return event_repo.find_many(query, skip=skip, limit=limit, sort=[("date", -1)])


@router.post("/delay-events", status_code=status.HTTP_201_CREATED)
def create_delay_event(
    payload: DelayEventCreate,
    current_user: dict = Depends(require_role(["analyst", "admin"])),
    event_repo: DelayEventRepository = Depends(get_event_repo),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    doc = payload.model_dump()
    doc["created_by"] = current_user["id"]
    doc["created_at"] = datetime.now(timezone.utc)
    ev_id = event_repo.insert_one(doc)

    audit_repo.log_event(
        action="DELAY_EVENT_CREATED",
        entity_type="delay_event",
        entity_id=ev_id,
        user_id=current_user["id"],
        user_email=current_user["email"],
        details={"route_no": payload.route_no, "cause": payload.cause, "minutes": payload.minutes},
    )
    doc["id"] = ev_id
    return doc
