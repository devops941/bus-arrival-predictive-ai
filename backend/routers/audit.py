"""
Audit Log Router (Admin Only).
Allows administrators to inspect system access, mutations, and authentication history.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from backend.deps import require_role, get_audit_repository
from src.db.repositories.audit_repo import AuditRepository
from backend.schemas import AuditLogResponse


router = APIRouter(prefix="/audit-log", tags=["Audit Log"])


@router.get("", response_model=List[AuditLogResponse])
def get_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action code"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_admin: dict = Depends(require_role(["admin"])),
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    """Retrieve system audit logs. Requires Admin privileges."""
    logs = audit_repo.list_logs(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        skip=skip,
        limit=limit,
    )
    return [
        AuditLogResponse(
            id=l["id"],
            timestamp=l["timestamp"],
            action=l["action"],
            entity_type=l["entity_type"],
            entity_id=l.get("entity_id"),
            user_id=l.get("user_id"),
            user_email=l.get("user_email", "anonymous"),
            details=l.get("details", {}),
            ip_address=l.get("ip_address"),
        )
        for l in logs
    ]
