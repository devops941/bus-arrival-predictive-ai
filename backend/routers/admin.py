"""
Administrative Management API Router (Admin Only).
Provides user role management, account activation, system metrics, and audit inspection.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import os
import sys
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from backend.deps import require_role, get_db
from src.config import get_settings
from src.db.repositories.user_repo import UserRepository
from src.db.repositories.audit_repo import AuditRepository


router = APIRouter(prefix="/admin", tags=["Administration"])


class RoleUpdateRequest(BaseModel):
    role: str = Field(..., description="Target role: passenger, analyst, admin")


class UserStatusUpdateRequest(BaseModel):
    is_active: bool


@router.get("/users")
def get_all_users(
    role: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_admin: dict = Depends(require_role(["admin"])),
    db=Depends(get_db),
):
    """List all user accounts with role, failed attempts, and lockout status."""
    user_repo = UserRepository(db)
    users = user_repo.list_users(skip=skip, limit=limit, role=role)
    cleaned = []
    for u in users:
        cleaned.append({
            "id": u["id"],
            "email": u["email"],
            "full_name": u.get("full_name", ""),
            "role": u.get("role", "passenger"),
            "is_active": u.get("is_active", True),
            "failed_login_attempts": u.get("failed_login_attempts", 0),
            "is_locked": user_repo.is_locked(u),
            "locked_until": u.get("locked_until"),
            "created_at": u.get("created_at"),
        })
    return cleaned


@router.put("/users/{id}/role")
def update_user_role(
    id: str,
    payload: RoleUpdateRequest,
    current_admin: dict = Depends(require_role(["admin"])),
    db=Depends(get_db),
):
    """Change user role. Requires administrator privileges."""
    target_role = payload.role.lower().strip()
    if target_role not in ("passenger", "analyst", "admin"):
        raise HTTPException(status_code=400, detail={"detail": "Invalid role. Must be passenger, analyst, or admin.", "code": "INVALID_ROLE"})

    user_repo = UserRepository(db)
    audit_repo = AuditRepository(db)

    user = user_repo.find_by_id(id)
    if not user:
        raise HTTPException(status_code=404, detail={"detail": "User not found", "code": "NOT_FOUND"})

    user_repo.update_by_id(id, {"role": target_role, "updated_at": datetime.now(timezone.utc)})

    audit_repo.log_event(
        action="USER_ROLE_CHANGED",
        entity_type="user",
        entity_id=id,
        user_id=current_admin["id"],
        user_email=current_admin["email"],
        details={"target_email": user["email"], "new_role": target_role},
    )
    return {"detail": f"User role updated to '{target_role}'", "user_id": id, "new_role": target_role}


@router.put("/users/{id}/status")
def update_user_status(
    id: str,
    payload: UserStatusUpdateRequest,
    current_admin: dict = Depends(require_role(["admin"])),
    db=Depends(get_db),
):
    """Activate or deactivate user account."""
    user_repo = UserRepository(db)
    audit_repo = AuditRepository(db)

    user = user_repo.find_by_id(id)
    if not user:
        raise HTTPException(status_code=404, detail={"detail": "User not found", "code": "NOT_FOUND"})

    user_repo.update_by_id(id, {"is_active": payload.is_active, "updated_at": datetime.now(timezone.utc)})

    audit_repo.log_event(
        action="USER_STATUS_TOGGLED",
        entity_type="user",
        entity_id=id,
        user_id=current_admin["id"],
        user_email=current_admin["email"],
        details={"target_email": user["email"], "is_active": payload.is_active},
    )
    return {"detail": f"User active status set to {payload.is_active}", "user_id": id}


@router.get("/jobs")
def get_system_jobs(
    limit: int = Query(50, ge=1, le=200),
    current_admin: dict = Depends(require_role(["admin"])),
    db=Depends(get_db),
):
    """List background job execution runs."""
    jobs_coll = db["job_runs"]
    jobs = list(jobs_coll.find({}).sort([("created_at", -1)]).limit(limit))
    for j in jobs:
        if "_id" in j:
            j["id"] = str(j["_id"])
            j["_id"] = str(j["_id"])
    return jobs


@router.get("/system")
def get_system_diagnostics(
    current_admin: dict = Depends(require_role(["admin"])),
    db=Depends(get_db),
):
    """Retrieve operational diagnostics and collection document counts."""
    settings = get_settings()

    collections = [
        "users", "routes", "stops", "route_stops", "trips",
        "observations", "delay_events", "models", "predictions_log", "alerts", "reports", "audit_log"
    ]
    counts = {}
    for c in collections:
        try:
            counts[c] = db[c].count_documents({})
        except Exception:
            counts[c] = len(list(db[c].find({})))

    active_model = db["models"].find_one({"status": "active"})
    model_name = active_model.get("name") if active_model else "None (No active model)"

    return {
        "status": "operational",
        "app_env": settings.APP_ENV,
        "database_name": db.name,
        "active_model": model_name,
        "collection_counts": counts,
        "scheduler_enabled": settings.SCHEDULER_ENABLED,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
