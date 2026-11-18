"""
Arrival Observation and Delay Event Repositories for MongoDB.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pymongo import UpdateOne
from pymongo.database import Database
from src.db.repositories.base import BaseRepository


class ObservationRepository(BaseRepository):
    def __init__(self, db: Optional[Database] = None):
        super().__init__("observations", db)

    def bulk_upsert_observations(self, observations: List[Dict[str, Any]]) -> int:
        """
        Idempotently upsert arrival observations using compound key (trip_id, stop_code).
        Updates delay_min, actual_arrival, and outlier flags if record already exists.
        """
        if not observations:
            return 0
        ops = []
        now = datetime.now(timezone.utc)
        for obs in observations:
            doc = dict(obs)
            created_at = doc.pop("created_at", now)
            doc["updated_at"] = now
            ops.append(
                UpdateOne(
                    {"trip_id": doc["trip_id"], "stop_code": doc["stop_code"]},
                    {"$set": doc, "$setOnInsert": {"created_at": created_at}},
                    upsert=True
                )
            )
        res = self.collection.bulk_write(ops, ordered=False)
        return (res.upserted_count or 0) + (res.modified_count or 0)

    def get_observations(
        self,
        route_no: Optional[str] = None,
        stop_code: Optional[str] = None,
        trip_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {}
        if route_no:
            query["route_no"] = str(route_no).strip()
        if stop_code:
            query["stop_code"] = str(stop_code).strip()
        if trip_id:
            query["trip_id"] = str(trip_id).strip()
        if date_from or date_to:
            time_filter = {}
            if date_from:
                time_filter["$gte"] = date_from
            if date_to:
                time_filter["$lte"] = date_to
            query["scheduled_arrival"] = time_filter

        return self.find_many(query, skip=skip, limit=limit, sort=[("scheduled_arrival", -1)])


class DelayEventRepository(BaseRepository):
    def __init__(self, db: Optional[Database] = None):
        super().__init__("delay_events", db)

    def bulk_upsert_events(self, events: List[Dict[str, Any]]) -> int:
        """Idempotently insert/upsert delay events."""
        if not events:
            return 0
        ops = []
        now = datetime.now(timezone.utc)
        for e in events:
            doc = dict(e)
            created_at = doc.pop("created_at", now)
            doc["updated_at"] = now
            ops.append(
                UpdateOne(
                    {"date": doc["date"], "time": doc["time"], "route_no": doc.get("route_no")},
                    {"$set": doc, "$setOnInsert": {"created_at": created_at}},
                    upsert=True
                )
            )
        res = self.collection.bulk_write(ops, ordered=False)
        return (res.upserted_count or 0) + (res.modified_count or 0)
