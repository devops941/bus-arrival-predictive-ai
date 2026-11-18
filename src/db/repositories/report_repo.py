"""
Report Management Repository for MongoDB.
Tracks generated PDF, Excel, and CSV report artifacts.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pymongo.database import Database
from src.db.repositories.base import BaseRepository


class ReportRepository(BaseRepository):
    def __init__(self, db: Optional[Database] = None):
        super().__init__("reports", db)

    def save_report_record(
        self,
        report_id: str,
        title: str,
        kind: str,
        file_format: str,
        file_path: str,
        row_count: int,
        author: str,
        author_id: Optional[str] = None,
    ) -> str:
        doc = {
            "report_id": report_id,
            "title": title,
            "kind": kind,
            "file_format": file_format,
            "file_path": file_path,
            "row_count": row_count,
            "author": author,
            "author_id": author_id,
            "created_at": datetime.now(timezone.utc),
        }
        return self.insert_one(doc)

    def get_by_report_id(self, report_id: str) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        query: List[Dict[str, Any]] = [{"report_id": report_id}, {"id": report_id}]
        try:
            query.append({"_id": ObjectId(report_id)})
        except Exception:
            pass
        return self.find_one({"$or": query})
