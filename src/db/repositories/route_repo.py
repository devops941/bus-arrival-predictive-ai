"""
Route, Stop, and Route-Stop Repositories for MongoDB.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pymongo import UpdateOne
from pymongo.database import Database
from src.db.repositories.base import BaseRepository


class RouteRepository(BaseRepository):
    def __init__(self, db: Optional[Database] = None):
        super().__init__("routes", db)

    def get_by_route_no(self, route_no: str) -> Optional[Dict[str, Any]]:
        return self.find_one({"route_no": str(route_no).strip()})

    def bulk_upsert_routes(self, routes: List[Dict[str, Any]]) -> int:
        """Idempotently upsert routes using unique route_no."""
        if not routes:
            return 0
        ops = []
        now = datetime.now(timezone.utc)
        for r in routes:
            doc = dict(r)
            created_at = doc.pop("created_at", now)
            doc["updated_at"] = now
            ops.append(
                UpdateOne(
                    {"route_no": doc["route_no"]},
                    {"$set": doc, "$setOnInsert": {"created_at": created_at}},
                    upsert=True
                )
            )
        res = self.collection.bulk_write(ops, ordered=False)
        return (res.upserted_count or 0) + (res.modified_count or 0)


class StopRepository(BaseRepository):
    def __init__(self, db: Optional[Database] = None):
        super().__init__("stops", db)

    def get_by_code(self, stop_code: str) -> Optional[Dict[str, Any]]:
        return self.find_one({"stop_code": str(stop_code).strip()})

    def bulk_upsert_stops(self, stops: List[Dict[str, Any]]) -> int:
        """Idempotently upsert stops using unique stop_code."""
        if not stops:
            return 0
        ops = []
        now = datetime.now(timezone.utc)
        for s in stops:
            doc = dict(s)
            created_at = doc.pop("created_at", now)
            doc["updated_at"] = now
            ops.append(
                UpdateOne(
                    {"stop_code": doc["stop_code"]},
                    {"$set": doc, "$setOnInsert": {"created_at": created_at}},
                    upsert=True
                )
            )
        res = self.collection.bulk_write(ops, ordered=False)
        return (res.upserted_count or 0) + (res.modified_count or 0)


class RouteStopRepository(BaseRepository):
    def __init__(self, db: Optional[Database] = None):
        super().__init__("route_stops", db)

    def get_stops_for_route(self, route_no: str) -> List[Dict[str, Any]]:
        return self.find_many({"route_no": str(route_no).strip()}, sort=[("sequence", 1)])

    def bulk_upsert_route_stops(self, route_stops: List[Dict[str, Any]]) -> int:
        """Idempotently upsert route stops using (route_no, sequence)."""
        if not route_stops:
            return 0
        ops = []
        now = datetime.now(timezone.utc)
        for rs in route_stops:
            doc = dict(rs)
            created_at = doc.pop("created_at", now)
            doc["updated_at"] = now
            ops.append(
                UpdateOne(
                    {"route_no": doc["route_no"], "sequence": doc["sequence"]},
                    {"$set": doc, "$setOnInsert": {"created_at": created_at}},
                    upsert=True
                )
            )
        res = self.collection.bulk_write(ops, ordered=False)
        return (res.upserted_count or 0) + (res.modified_count or 0)
