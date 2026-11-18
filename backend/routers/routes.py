"""
Route and Stop Management Routers.
Provides CRUD endpoints for transit routes, stops, and sequence mappings.
Audit logs all write actions.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from backend.deps import require_role, get_current_user, get_db
from src.db.repositories.route_repo import RouteRepository, StopRepository, RouteStopRepository
from src.db.repositories.audit_repo import AuditRepository


router = APIRouter(tags=["Transit Network"])


# Pydantic Schemas
class RouteCreate(BaseModel):
    route_no: str = Field(..., description="Unique route identifier, e.g. '101'")
    name: str = Field(..., description="Route name, e.g. 'Metro Express'")
    origin: str
    destination: str
    total_distance_km: float = Field(..., gt=0)
    scheduled_headway_min: int = Field(..., gt=0)
    active: bool = True


class RouteUpdate(BaseModel):
    name: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    total_distance_km: Optional[float] = Field(None, gt=0)
    scheduled_headway_min: Optional[int] = Field(None, gt=0)
    active: Optional[bool] = None


class StopCreate(BaseModel):
    stop_code: str = Field(..., description="Unique stop code, e.g. 'ST-001'")
    name: str
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)


class RouteStopCreate(BaseModel):
    route_no: str
    stop_code: str
    sequence: int = Field(..., ge=1)
    distance_from_start_km: float = Field(..., ge=0.0)
    scheduled_offset_min: int = Field(..., ge=0)


# Dependencies
def get_route_repo(db=Depends(get_db)) -> RouteRepository:
    return RouteRepository(db)


def get_stop_repo(db=Depends(get_db)) -> StopRepository:
    return StopRepository(db)


def get_route_stop_repo(db=Depends(get_db)) -> RouteStopRepository:
    return RouteStopRepository(db)


def get_audit_repo(db=Depends(get_db)) -> AuditRepository:
    return AuditRepository(db)


# Route Endpoints
@router.get("/routes")
def list_routes(
    active_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    route_repo: RouteRepository = Depends(get_route_repo),
    route_stop_repo: RouteStopRepository = Depends(get_route_stop_repo),
):
    query = {"active": True} if active_only else {}
    routes = route_repo.find_many(query, skip=skip, limit=limit, sort=[("route_no", 1)])
    for r in routes:
        rs_list = route_stop_repo.get_stops_for_route(r.get("route_no", ""))
        r["stops"] = [
            {
                "stop_id": rs.get("stop_code"),
                "sequence": rs.get("sequence", 1),
                "distance_from_origin_km": rs.get("distance_from_start_km", 0.0),
                "scheduled_travel_min": rs.get("scheduled_offset_min", 0),
            }
            for rs in rs_list
        ]
        r["stops_count"] = len(rs_list)
    return routes


@router.post("/routes", status_code=status.HTTP_201_CREATED)
def create_route(
    payload: RouteCreate,
    current_user: dict = Depends(require_role(["analyst", "admin"])),
    route_repo: RouteRepository = Depends(get_route_repo),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    existing = route_repo.get_by_route_no(payload.route_no)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": f"Route '{payload.route_no}' already exists", "code": "ROUTE_EXISTS"},
        )

    doc = payload.model_dump()
    doc["created_by"] = current_user["id"]
    doc["created_at"] = datetime.now(timezone.utc)
    route_id = route_repo.insert_one(doc)

    audit_repo.log_event(
        action="ROUTE_CREATED",
        entity_type="route",
        entity_id=route_id,
        user_id=current_user["id"],
        user_email=current_user["email"],
        details={"route_no": payload.route_no},
    )
    doc["id"] = route_id
    return doc


@router.get("/routes/{id}")
def get_route(
    id: str,
    route_repo: RouteRepository = Depends(get_route_repo),
    route_stop_repo: RouteStopRepository = Depends(get_route_stop_repo),
):
    r = route_repo.find_by_id(id) or route_repo.get_by_route_no(id)
    if not r:
        raise HTTPException(status_code=404, detail={"detail": "Route not found", "code": "NOT_FOUND"})
    rs_list = route_stop_repo.get_stops_for_route(r.get("route_no", ""))
    r["stops"] = [
        {
            "stop_id": rs.get("stop_code"),
            "sequence": rs.get("sequence", 1),
            "distance_from_origin_km": rs.get("distance_from_start_km", 0.0),
            "scheduled_travel_min": rs.get("scheduled_offset_min", 0),
        }
        for rs in rs_list
    ]
    r["stops_count"] = len(rs_list)
    return r


@router.put("/routes/{id}")
def update_route(
    id: str,
    payload: RouteUpdate,
    current_user: dict = Depends(require_role(["analyst", "admin"])),
    route_repo: RouteRepository = Depends(get_route_repo),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    r = route_repo.find_by_id(id) or route_repo.get_by_route_no(id)
    if not r:
        raise HTTPException(status_code=404, detail={"detail": "Route not found", "code": "NOT_FOUND"})

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc)
    route_repo.update_by_id(r["id"], updates)

    audit_repo.log_event(
        action="ROUTE_UPDATED",
        entity_type="route",
        entity_id=r["id"],
        user_id=current_user["id"],
        user_email=current_user["email"],
        details=updates,
    )
    return route_repo.find_by_id(r["id"])


@router.delete("/routes/{id}")
def delete_route(
    id: str,
    current_user: dict = Depends(require_role(["admin"])),
    route_repo: RouteRepository = Depends(get_route_repo),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    r = route_repo.find_by_id(id) or route_repo.get_by_route_no(id)
    if not r:
        raise HTTPException(status_code=404, detail={"detail": "Route not found", "code": "NOT_FOUND"})

    route_repo.delete_by_id(r["id"])
    audit_repo.log_event(
        action="ROUTE_DELETED",
        entity_type="route",
        entity_id=r["id"],
        user_id=current_user["id"],
        user_email=current_user["email"],
    )
    return {"detail": "Route deleted successfully"}


# Stop Endpoints
@router.get("/stops")
def list_stops(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    stop_repo: StopRepository = Depends(get_stop_repo),
):
    return stop_repo.find_many({}, skip=skip, limit=limit, sort=[("stop_code", 1)])


@router.post("/stops", status_code=status.HTTP_201_CREATED)
def create_stop(
    payload: StopCreate,
    current_user: dict = Depends(require_role(["analyst", "admin"])),
    stop_repo: StopRepository = Depends(get_stop_repo),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    existing = stop_repo.get_by_code(payload.stop_code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": f"Stop code '{payload.stop_code}' already exists", "code": "STOP_EXISTS"},
        )

    doc = payload.model_dump()
    doc["created_by"] = current_user["id"]
    doc["created_at"] = datetime.now(timezone.utc)
    stop_id = stop_repo.insert_one(doc)

    audit_repo.log_event(
        action="STOP_CREATED",
        entity_type="stop",
        entity_id=stop_id,
        user_id=current_user["id"],
        user_email=current_user["email"],
        details={"stop_code": payload.stop_code},
    )
    doc["id"] = stop_id
    return doc


# Route-Stop Endpoints
@router.get("/route-stops")
def list_route_stops(
    route_no: Optional[str] = None,
    route_stop_repo: RouteStopRepository = Depends(get_route_stop_repo),
):
    if route_no:
        return route_stop_repo.get_stops_for_route(route_no)
    return route_stop_repo.find_many({}, limit=500, sort=[("route_no", 1), ("sequence", 1)])


@router.post("/route-stops", status_code=status.HTTP_201_CREATED)
def create_route_stop(
    payload: RouteStopCreate,
    current_user: dict = Depends(require_role(["analyst", "admin"])),
    route_stop_repo: RouteStopRepository = Depends(get_route_stop_repo),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    doc = payload.model_dump()
    doc["created_at"] = datetime.now(timezone.utc)
    rs_id = route_stop_repo.insert_one(doc)

    audit_repo.log_event(
        action="ROUTE_STOP_CREATED",
        entity_type="route_stop",
        entity_id=rs_id,
        user_id=current_user["id"],
        user_email=current_user["email"],
        details={"route_no": payload.route_no, "sequence": payload.sequence},
    )
    doc["id"] = rs_id
    return doc
