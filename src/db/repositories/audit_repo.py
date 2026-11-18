"""
Audit Repository for MongoDB.
Records and tracks all system modifications, data imports, and authentication events.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pymongo.database import Database
from src.db.repositories.base import BaseRepository


class AuditRepository(BaseRepository):
    def __init__(self, db: Optional[Database] = None):
        super().__init__("audit_log", db)

    def log_event(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> str:
        """Record an event into the audit log."""
        doc = {
            "timestamp": datetime.now(timezone.utc),
            "action": action,
            "entity_type": entity_type,
            "entity_id": str(entity_id) if entity_id else None,
            "user_id": str(user_id) if user_id else None,
            "user_email": user_email or "anonymous",
            "details": details or {},
            "ip_address": ip_address or "127.0.0.1",
        }
        return self.insert_one(doc)

    def list_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query audit logs with optional filters."""
        query: Dict[str, Any] = {}
        if user_id:
            query["user_id"] = user_id
        if action:
            query["action"] = action
        if entity_type:
            query["entity_type"] = entity_type

        return self.find_many(query, skip=skip, limit=limit, sort=[("timestamp", -1)])
