"""
Trip Repository for MongoDB.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pymongo import UpdateOne
from pymongo.database import Database
from src.db.repositories.base import BaseRepository


class TripRepository(BaseRepository):
    def __init__(self, db: Optional[Database] = None):
        super().__init__("trips", db)

    def get_by_trip_id(self, trip_id: str) -> Optional[Dict[str, Any]]:
        return self.find_one({"trip_id": str(trip_id).strip()})

    def bulk_upsert_trips(self, trips: List[Dict[str, Any]]) -> int:
        """Idempotently upsert trips using unique trip_id."""
        if not trips:
            return 0
        ops = []
        now = datetime.now(timezone.utc)
        for t in trips:
            doc = dict(t)
            created_at = doc.pop("created_at", now)
            doc["updated_at"] = now
            ops.append(
                UpdateOne(
                    {"trip_id": doc["trip_id"]},
                    {"$set": doc, "$setOnInsert": {"created_at": created_at}},
                    upsert=True
                )
            )
        res = self.collection.bulk_write(ops, ordered=False)
        return (res.upserted_count or 0) + (res.modified_count or 0)
